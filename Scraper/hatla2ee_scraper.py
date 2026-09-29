from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, SoupStrainer


BASE_URL = "https://eg.hatla2ee.com/en/car/search"
FUEL_TYPES = ["gas", "diesel", "natural gas", "electric", "hybrid"]
PROPERTIES = ["brand", "model", "color", "class", "km", "city"]
FUEL_LABELS = {"gas", "diesel", "natural gas", "electric", "hybrid"}
TRANSMISSIONS = {"automatic", "manual"}


def _clean_text(value: str | None) -> str:
    return value.strip() if value else ""


def _output_path(output_dir: str) -> Path:
    now = datetime.now()
    file_name = f"{now:%d-%m-%Y}.csv"
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path / file_name


def _checkpoint_path(output_path: Path) -> Path:
    return output_path.with_suffix(".checkpoint.json")


def _load_seen_ids(output_path: Path) -> set[str]:
    if not output_path.exists() or output_path.stat().st_size == 0:
        return set()

    try:
        existing = pd.read_csv(output_path, usecols=["id"])
    except Exception:
        return set()

    return set(existing["id"].astype(str))


def _load_checkpoint(checkpoint_path: Path) -> dict:
    if not checkpoint_path.exists():
        return {"fuel_index": 0, "page": 1}

    try:
        return json.loads(checkpoint_path.read_text())
    except Exception:
        return {"fuel_index": 0, "page": 1}


def _save_checkpoint(checkpoint_path: Path, fuel_index: int, page: int) -> None:
    checkpoint_path.write_text(json.dumps({"fuel_index": fuel_index, "page": page}))


def _append_rows(output_path: Path, rows: list[dict]) -> None:
    if not rows:
        return

    frame = pd.DataFrame(rows)
    write_header = not output_path.exists() or output_path.stat().st_size == 0
    frame.to_csv(output_path, mode="a", header=write_header, index=False)


def get_page(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _pages_count(soup: BeautifulSoup) -> int:
    pagination = soup.select_one('nav[aria-label="pagination"]')
    if pagination is None:
        return 1

    page_numbers = []
    for link in pagination.select('a[href*="page="]'):
        href = str(link.get("href"))
        match = re.search(r"[?&]page=(\d+)", href)
        if match:
            page_numbers.append(int(match.group(1)))

    return max(page_numbers, default=1)


def _parse_listing(card: BeautifulSoup, fuel: str) -> dict | None:
    link = card.select_one('a[href^="/en/car/"]')
    if link is None:
        return None

    car_link = str(link.get("href"))
    car_id_match = re.search(r"/en/car/[^/]+/[^/]+/(\d+)$", car_link)
    if car_id_match is None:
        return None

    detail = card.select_one('div.flex.flex-col.flex-1')
    if detail is None:
        return None

    raw_text = " ".join(_clean_text(item) for item in detail.stripped_strings)
    if "EGP" not in raw_text:
        return None

    title_tag = detail.find("a")
    title = _clean_text(title_tag.get_text(" ", strip=True) if title_tag else None)
    year_match = re.search(r"(19\d{2}|20\d{2})", title)
    year = year_match.group(1) if year_match else ""

    tokens = [_clean_text(token) for token in detail.stripped_strings]
    tokens = [token for token in tokens if token]

    km = next((token for token in tokens if "KM" in token.upper()), "")

    transmission_token = next((token for token in tokens if token.lower() in TRANSMISSIONS), "")
    automatic = 1 if transmission_token.lower() == "automatic" else 0

    fuel_token = next((token for token in tokens if token.lower() in FUEL_LABELS), fuel)

    price_match = re.search(r"([\d,]+)\s*EGP", raw_text)
    if price_match is None:
        return None
    price = price_match.group(1).replace(",", "")

    location_tag = detail.select_one('a[href*="/city/"]')
    city = _clean_text(location_tag.get_text(" ", strip=True) if location_tag else "")

    brand_tag = None
    model_tag = None
    for anchor in detail.select('a[href^="/en/car/"]'):
        href = str(anchor.get("href"))
        if brand_tag is None and re.fullmatch(r"/en/car/[^/]+$", href):
            brand_tag = anchor
        elif model_tag is None and "/city/" not in href and re.fullmatch(r"/en/car/[^/]+/[^/]+$", href):
            model_tag = anchor

    brand = ""
    model = ""
    if brand_tag is not None:
        brand = _clean_text(brand_tag.get_text(" ", strip=True))

    if model_tag is not None:
        model = _clean_text(model_tag.get_text(" ", strip=True))

    car_id = car_id_match.group(1)
    keys = ["id", "title", "year", "ad_date", "transmission", "price", "fingerprint", "fuel"] + PROPERTIES
    values = [car_id, title, year, "", automatic, price, f"{car_id}-{price}", fuel_token, brand, model, "", "", km, city]
    return dict(zip(keys, values))


def scrape_cars(output_dir: str = "cars_raw_data") -> Path:
    session = requests.Session()
    output_path = _output_path(output_dir)
    checkpoint_path = _checkpoint_path(output_path)
    checkpoint = _load_checkpoint(checkpoint_path)
    seen_ids = _load_seen_ids(output_path)
    start_fuel_index = int(checkpoint.get("fuel_index", 0))
    start_page = int(checkpoint.get("page", 1))
    total_saved = len(seen_ids)

    for index, fuel in enumerate(FUEL_TYPES[start_fuel_index:], start=start_fuel_index):
        url = f"{BASE_URL}?fuel={index + 1}&page="
        soup = get_page(session, url)
        pages_no = _pages_count(soup)
        page_start = start_page if index == start_fuel_index else 1

        for page in range(page_start, pages_no + 1):
            url = f"{BASE_URL}?fuel={index + 1}&page={page}"
            soup = get_page(session, url)
            car_list = soup.find_all(attrs={"class": "newCarListUnit_data_wrap"})
            if not car_list:
                car_list = soup.select('div[data-slot="card"]')

            page_rows: list[dict] = []

            for child in car_list:
                car_info = _parse_listing(child, fuel)
                if car_info is None:
                    continue

                if car_info["id"] in seen_ids:
                    continue

                seen_ids.add(car_info["id"])
                page_rows.append(car_info)
                total_saved += 1
                print(total_saved)

            _append_rows(output_path, page_rows)

            if page < pages_no:
                _save_checkpoint(checkpoint_path, index, page + 1)
            else:
                _save_checkpoint(checkpoint_path, index + 1, 1)

    if checkpoint_path.exists():
        checkpoint_path.unlink()

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Hatla2ee used car listings into CSV.")
    parser.add_argument("--output-dir", default="cars_raw_data", help="Directory to write the CSV file")
    parser.add_argument("--reset", action="store_true", help="Ignore any saved checkpoint and start over")
    args = parser.parse_args()

    output_path = _output_path(args.output_dir)
    checkpoint_path = _checkpoint_path(output_path)

    if args.reset:
        if output_path.exists():
            output_path.unlink()
        if checkpoint_path.exists():
            checkpoint_path.unlink()

    final_path = scrape_cars(args.output_dir)
    saved_rows = 0
    if final_path.exists() and final_path.stat().st_size > 0:
        saved_rows = len(pd.read_csv(final_path))
    print(f"Saved {saved_rows} cars to {final_path}")


if __name__ == "__main__":
    main()