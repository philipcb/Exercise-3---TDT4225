import pandas as pd
from common import DATA_DIR, load_movies, save_table


def analyze_file_ids(movies):
    movie_ids = set(movies["id"])

    rows = []
    for name in ["credits.csv", "keywords.csv"]:
        df = pd.read_csv(DATA_DIR / name)
        ids = set(df["id"])
        rows.append((name, len(df), len(ids), df.duplicated().sum(), len(ids - movie_ids), len(movie_ids - ids)))

    save_table(rows, "id_chain", "file_ids.csv",
               ["File", "Rows", "Unique ids", "Exact duplicate rows", "Ids not in movies_metadata",
                "Movies without row"])


def analyze_links(movies):
    links = pd.read_csv(DATA_DIR / "links.csv")
    tmdb_counts = links["tmdbId"].value_counts()

    summary = [
        ["Rows", len(links)],
        ["Missing tmdbId", links["tmdbId"].isna().sum()],
        ["tmdbId not in movies_metadata", (links["tmdbId"].notna() & ~links["tmdbId"].isin(movies["id"])).sum()],
        ["tmdbIds shared by several movieIds", (tmdb_counts > 1).sum()],
    ]
    save_table(summary, "id_chain", "links.csv", ["Measure", "Count"])


def main():
    movies = load_movies().drop_duplicates("id")
    analyze_file_ids(movies)
    analyze_links(movies)


if __name__ == '__main__':
    main()
