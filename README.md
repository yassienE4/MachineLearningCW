# Used-car price predictor


```
├── Data/
│   ├── clean/
│   │   └── 2026-05-25_used_cars_cleaned.csv
│   ├── model_ready/
│   │   └── 2026-05-25/
│   │       ├── used_cars_feature_names.csv
│   │       ├── used_cars_preprocessing_pipeline.joblib
│   │       ├── used_cars_x_test.npz
│   │       ├── used_cars_x_train.npz
│   │       ├── used_cars_y_test.csv
│   │       └── used_cars_y_train.csv
│   ├── preprocessed/
│   │   └── 2026-05-25_used_cars_preprocessed.csv
│   └── raw/
│       ├── 2026-05-25_used_cars_raw.csv
│       └── 2026-10-13_used_cars_raw.csv
├── Notebooks/
│   └── phase1/
│       ├── clean_data.ipynb
│       ├── data_collection.ipynb
│       ├── exploratory_data_analysis.ipynb
│       ├── model_preparation.ipynb
│       └── preprocessing.ipynb
├── Scraper/
│   ├── clean_used_cars_csv.py
│   └── hatla2ee_scraper.py
├── .gitignore
└── README.md
```