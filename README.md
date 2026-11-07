# Used-car price predictor

Predicting the advertised price (EGP) of used cars in Egypt, as a regression problem.

- **Dataset source:** listings scraped from Hatla2ee, https://eg.hatla2ee.com/en/car/search
- **Dataset files:** `Data/raw/` (scraper output) and `Data/clean/` (de-duplicated). The results use the `2026-10-13` snapshot.
- **Notebook:** [`Notebooks/used_car_price_prediction.ipynb`](Notebooks/used_car_price_prediction.ipynb), the end-to-end pipeline: data collection, EDA, preprocessing, K-Means feature engineering, model training, hyperparameter tuning and evaluation.

```
├── Data/
│   ├── clean/
│   │   └── Date_used_cars_cleaned.csv
│   └── raw/
│       └── Date_used_cars_raw.csv
├── Notebooks/
│   └── used_car_price_prediction.ipynb
├── Report/
│   └── Draft1/
├── Scraper/
│   ├── clean_used_cars_csv.py
│   └── hatla2ee_scraper.py
├── .gitignore
└── README.md
```
