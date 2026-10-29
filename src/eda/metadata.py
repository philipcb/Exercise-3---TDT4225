import ast
import pandas as pd
from common import load_movies, save_table


def analyze_missing_data(movies):
    rows = []
    for column in ["budget", "revenue", "runtime", "vote_count", "release_date", "genres"]:
        values = movies[column]
        rows.append((column, values.isna().sum(), (values == 0).sum(), (values == "[]").sum()))
    save_table(rows, "metadata", "missing_by_column.csv", ["Column", "Missing", "Zero", "Empty list"])

    popular = movies[(movies["vote_count"] >= 1000) & (movies["budget"] > 0)]
    summary = [
        ["Movies with vote_count >= 1000 and budget > 0", len(popular)],
        ["...with revenue = 0", (popular["revenue"] == 0).sum()],
    ]
    save_table(summary, "metadata", "zero_revenue_test.csv", ["Measure", "Count"])


def analyze_value_ranges(movies):
    stats = movies[["budget", "revenue", "runtime", "popularity", "vote_average", "vote_count"]].describe()
    save_table(stats.round(2).reset_index(names="Statistic"), "metadata", "value_ranges.csv")

    runtime = movies["runtime"]
    rows = [
        ["0", (runtime == 0).sum()],
        ["1-40", runtime.between(1, 40).sum()],
        ["41-180", runtime.between(41, 180).sum()],
        ["> 180", (runtime > 180).sum()],
    ]
    save_table(rows, "metadata", "runtime_buckets.csv", ["Runtime (minutes)", "Movies"])


def analyze_genres(movies):
    genre_counts = {}
    for genres in movies["genres"]:
        for genre in ast.literal_eval(genres):
            genre_counts[genre["name"]] = genre_counts.get(genre["name"], 0) + 1

    rows = sorted(genre_counts.items(), key=lambda item: -item[1])
    save_table(rows, "metadata", "movies_per_genre.csv", ["Genre", "Movies"])


def analyze_vote_average(movies):
    summary = [
        ["vote_count = 0 and vote_average != 0", ((movies["vote_count"] == 0) & (movies["vote_average"] != 0)).sum()],
        ["vote_count > 0 and vote_average = 0", ((movies["vote_count"] > 0) & (movies["vote_average"] == 0)).sum()],
    ]
    save_table(summary, "metadata", "vote_average_vs_vote_count.csv", ["Measure", "Movies"])


def analyze_small_revenue(movies):
    small = movies.loc[(movies["revenue"] > 0) & (movies["revenue"] < 1000), "revenue"].astype(int)
    save_table([["0 < revenue < 1000", len(small)]], "metadata", "small_revenue.csv", ["Measure", "Movies"])

    rows = sorted(small.value_counts().items(), key=lambda item: (-item[1], item[0]))
    save_table(rows[:10], "metadata", "small_revenue_values.csv", ["Revenue", "Movies"])


def analyze_release_date_and_status(movies):
    release_date = pd.to_datetime(movies["release_date"], format="%Y-%m-%d", errors="coerce")

    # The dataset is said to only contain movies released up to July 2017
    summary = [
        ["release_date after 2017-07-31", (release_date > "2017-07-31").sum()],
        ["Without status", movies["status"].isna().sum()],
    ]
    save_table(summary, "metadata", "release_date_and_status.csv", ["Measure", "Movies"])
    save_table(movies["status"].value_counts().items(), "metadata", "status_counts.csv", ["Status", "Movies"])


def main():
    movies = load_movies().drop_duplicates("id")
    analyze_missing_data(movies)
    analyze_value_ranges(movies)
    analyze_genres(movies)
    analyze_vote_average(movies)
    analyze_small_revenue(movies)
    analyze_release_date_and_status(movies)


if __name__ == '__main__':
    main()
