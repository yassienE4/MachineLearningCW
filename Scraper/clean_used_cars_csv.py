from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_COLUMNS = [
    "id",
    "title",
    "year",
    "ad_date",
    "transmission",
    "price",
    "fingerprint",
    "fuel",
    "brand",
    "model",
    "color",
    "class",
    "km",
    "city",
]


def _read_cars_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise ValueError(f"Raw cars CSV is missing or empty: {path}")

    first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0].strip()
    columns_in_file = [part.strip() for part in first_line.split(",")]

    if columns_in_file == DEFAULT_COLUMNS:
        return pd.read_csv(path)

    return pd.read_csv(path, header=None, names=DEFAULT_COLUMNS)


def clean_cars(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Normalize a scraped cars CSV and remove duplicate listings.

    This intentionally retains every car regardless of price, transmission,
    fuel, or any other listing attribute so the result can be used as a full
    training corpus.
    """
    df = _read_cars_csv(input_path)

    df = df.drop_duplicates()

    if "fingerprint" in df.columns:
        df = df.drop_duplicates(subset=["fingerprint"])
    elif "id" in df.columns:
        df = df.drop_duplicates(subset=["id"])

    df = df.reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean a Hatla2ee cars CSV.")
    parser.add_argument("input", type=Path, help="Path to the raw CSV")
    parser.add_argument("output", type=Path, help="Path to the cleaned CSV")
    args = parser.parse_args()

    cleaned = clean_cars(input_path=args.input, output_path=args.output)
    print(f"Saved {len(cleaned)} rows to {args.output}")


if __name__ == "__main__":
    main()
