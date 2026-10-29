import pandas as pd
from common import DATA_DIR, load_movies, save_table


def analyze_ratings(movies, links, ratings):
    ratings_per_user = ratings["userId"].value_counts()
    ratings_per_movie = ratings["movieId"].value_counts()
    tmdb_ids = ratings["movieId"].map(dict(zip(links["movieId"], links["tmdbId"])))

    summary = [
        ["Ratings", len(ratings)],
        ["Users", len(ratings_per_user)],
        ["Movies (movieId)", len(ratings_per_movie)],
        ["Duplicate (userId, movieId)", ratings.duplicated(["userId", "movieId"]).sum()],
        ["Ratings without tmdbId in links", tmdb_ids.isna().sum()],
        ["Ratings with tmdbId not in movies_metadata", (tmdb_ids.notna() & ~tmdb_ids.isin(movies["id"])).sum()],
        ["Ratings where movieId is also a movies.id", ratings["movieId"].isin(movies["id"]).sum()],
        ["Ratings where movieId = tmdbId", (ratings["movieId"] == tmdb_ids).sum()],
    ]
    save_table(summary, "ratings", "ratings_summary.csv", ["Measure", "Count"])

    rating_counts = ratings["rating"].value_counts().sort_index()
    save_table(rating_counts.items(), "ratings", "rating_values.csv", ["Rating", "Ratings"])

    user_stats = ratings_per_user.describe()
    movie_stats = ratings_per_movie.describe()
    rows = []
    for statistic in user_stats.index:
        rows.append((statistic, round(user_stats[statistic], 2), round(movie_stats[statistic], 2)))
    save_table(rows, "ratings", "ratings_count_stats.csv", ["Statistic", "Ratings per user", "Ratings per movie"])


def main():
    movies = load_movies().drop_duplicates("id")
    links = pd.read_csv(DATA_DIR / "links.csv")
    ratings = pd.read_csv(DATA_DIR / "ratings.csv")
    analyze_ratings(movies, links, ratings)


if __name__ == '__main__':
    main()
