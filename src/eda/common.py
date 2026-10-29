from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "eda_results" / "tables"


def load_movies():
    movies = pd.read_csv(DATA_DIR / "movies_metadata.csv", low_memory=False)

    # The 3 movies that are split into two rows have no vote_count in either row
    movies = movies.dropna(subset=["vote_count"])
    movies["id"] = movies["id"].astype(int)
    movies["budget"] = movies["budget"].astype(int)
    movies["popularity"] = movies["popularity"].astype(float)
    return movies


def save_table(rows, folder, name, columns=None):
    path = RESULTS_DIR / folder
    path.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path / name, index=False)
