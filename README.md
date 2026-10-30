# Exercise 3 - TDT4225

Exploratory data analysis, MongoDB schema and queries for The Movies Dataset.

## Project structure

```
src/
  DbConnector.py         MongoDB connection, settings are read from .env
  insert_data.py         cleans the CSV files and inserts movies, ratings and precomputed users
  queries.py             tasks 1-10, results are saved to query_results/
  eda/                   EDA of the raw CSV files, results are saved to eda_results/
  setup/                 dataset download and MongoDB init script for Docker
data/                    the dataset CSV files (not included in the repo)
eda_results/tables/      EDA results after running `python src/eda/eda.py`
query_results/           query results after running `python src/queries.py`
```

## Setup

1. Create a virtual environment and install the packages:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Download the dataset from Kaggle to `data/`:
   ```
   python src/setup/download.py
   ```
3. Copy `.env.example` to `.env` and fill in the MongoDB settings.
4. Start MongoDB with `docker compose up -d`.

## Run order

The scripts can be run from any folder.

1. `python src/eda/eda.py` - EDA of the raw CSV files
2. `python src/insert_data.py` - drops the collections and inserts the cleaned data (takes about 5-6 minutes)
3. `python src/queries.py` - tasks 1-10
