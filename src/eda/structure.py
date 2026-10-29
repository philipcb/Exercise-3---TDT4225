import pandas as pd
from common import DATA_DIR, load_movies, save_table

FILES = ["movies_metadata.csv", "credits.csv", "keywords.csv", "links.csv", "ratings.csv"]


def inspect_structure():
    file_rows = []
    column_rows = []
    for name in FILES:
        df = pd.read_csv(DATA_DIR / name, low_memory=False)
        file_rows.append((name, df.shape[0], df.shape[1]))

        dtypes = df.dtypes
        missing = df.isna().sum()
        for column in df.columns:
            column_rows.append((name, column, str(dtypes[column]), missing[column]))

    save_table(file_rows, "structure", "files.csv", ["File", "Rows", "Columns"])
    save_table(column_rows, "structure", "file_columns.csv", ["File", "Column", "Type", "Missing values"])


def analyze_broken_rows():
    movies = pd.read_csv(DATA_DIR / "movies_metadata.csv", low_memory=False)

    broken = movies[movies["vote_count"].isna()]
    save_table(broken[["id", "imdb_id", "title", "vote_count"]], "structure", "broken_rows.csv")


def analyze_movie_ids(movies):
    duplicates = movies[movies.duplicated("id", keep=False)]
    exact_duplicates = movies[movies.duplicated(keep=False)]

    summary = [
        ["Rows", len(movies)],
        ["Unique ids", movies["id"].nunique()],
        ["Duplicate ids", duplicates["id"].nunique()],
        ["Rows with duplicate id", len(duplicates)],
        ["Exact duplicate rows", len(exact_duplicates)],
    ]
    save_table(summary, "structure", "movie_ids.csv", ["Measure", "Count"])

    duplicates = duplicates.sort_values("id")[["id", "title", "popularity", "vote_count"]]
    save_table(duplicates, "structure", "duplicate_ids.csv")


def main():
    inspect_structure()
    analyze_broken_rows()
    analyze_movie_ids(load_movies())


if __name__ == '__main__':
    main()
