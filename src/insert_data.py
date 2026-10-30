import ast
from collections import Counter
from pathlib import Path
import pandas as pd
from tabulate import tabulate
from DbConnector import DbConnector

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BATCH_SIZE = 10000

MIN_PLAUSIBLE_MONEY = 1000

summary = []


def load_movies():
    movies = pd.read_csv(DATA_DIR / "movies_metadata.csv", low_memory=False)
    print("Rows:", len(movies))

    rows = len(movies)
    movies = movies.dropna(subset=["vote_count"])
    summary.append(["movies: shifted rows dropped", rows - len(movies)])

    for column in ["id", "vote_count", "budget", "revenue", "runtime"]:
        movies[column] = pd.to_numeric(movies[column]).astype("Int64")
    for column in ["popularity", "vote_average"]:
        movies[column] = pd.to_numeric(movies[column]).astype(float)

    rows = len(movies)
    movies = movies.sort_values(
        "vote_count", ascending=False, kind="stable"
    ).drop_duplicates("id")
    summary.append(["movies: duplicate ids removed", rows - len(movies)])
    print("Rows after removing broken rows and duplicate ids:", len(movies))

    for column in ["budget", "revenue", "runtime"]:
        zero = movies[column] == 0
        movies.loc[zero, column] = pd.NA
        summary.append([column + ": 0 -> null", zero.sum()])

    rows = []
    for limit in [100, 1000, 10000, 100000]:
        rows.append(
            [limit, (movies["budget"] < limit).sum(), (movies["revenue"] < limit).sum()]
        )
    print(tabulate(rows, headers=["Positive values below", "budget", "revenue"]))
    for column in ["budget", "revenue"]:
        small = movies[column] < MIN_PLAUSIBLE_MONEY
        movies.loc[small, column] = pd.NA
        summary.append(
            [column + ": below %d -> null" % MIN_PLAUSIBLE_MONEY, small.sum()]
        )

    no_votes = movies["vote_count"] == 0
    movies.loc[no_votes, "vote_average"] = None
    summary.append(["vote_average: vote_count = 0 -> null", no_votes.sum()])


    movies["release_date"] = pd.to_datetime(
        movies["release_date"], format="%Y-%m-%d", errors="coerce"
    )
    movies["release_year"] = movies["release_date"].dt.year.astype("Int64")
    return movies


def to_none(value):
    if pd.isna(value):
        return None
    return value


def to_int(value):
    if pd.isna(value):
        return None
    return int(value)


def to_names(value):
    names = []
    for item in ast.literal_eval(value):
        names.append(item["name"])
    return names


def to_countries(value):
    countries = []
    for item in ast.literal_eval(value):
        countries.append({"iso_3166_1": item["iso_3166_1"], "name": item["name"]})
    return countries


def to_cast(value):
    cast = []
    seen_ids = set()
    for member in sorted(
        ast.literal_eval(value), key=lambda member: (member["order"], member["id"])
    ):
        if member["id"] in seen_ids:
            continue
        seen_ids.add(member["id"])
        cast.append(
            {
                "id": member["id"],
                "name": member["name"].strip(),
                "character": member["character"],
                "order": member["order"],
                "rank": len(cast),
                "gender": member["gender"] if member["gender"] != 0 else None,
            }
        )
    return cast


def to_crew(value):
    crew = []
    seen_jobs = set()
    for member in ast.literal_eval(value):
        job = member["job"].strip()
        if (member["id"], job) in seen_jobs:
            continue
        seen_jobs.add((member["id"], job))
        crew.append(
            {
                "id": member["id"],
                "name": member["name"].strip(),
                "job": job,
                "department": member["department"],
            }
        )
    return crew


def load_credits():
    credits = pd.read_csv(DATA_DIR / "credits.csv")

    rows = len(credits)
    credits = credits.drop_duplicates()
    summary.append(["credits: exact duplicate rows removed", rows - len(credits)])

    repeated = credits["id"].duplicated(keep=False)
    summary.append(
        [
            "credits: ids with conflicting rows resolved",
            credits.loc[repeated, "id"].nunique(),
        ]
    )
    credits["cast_size"] = 0
    credits.loc[repeated, "cast_size"] = credits.loc[repeated, "cast"].map(
        lambda value: len(ast.literal_eval(value))
    )
    return credits.sort_values(
        "cast_size", ascending=False, kind="stable"
    ).drop_duplicates("id")


def insert_movies(connection, movies):
    credits = load_credits()
    keywords = pd.read_csv(DATA_DIR / "keywords.csv")
    rows = len(keywords)
    keywords = keywords.drop_duplicates("id")
    summary.append(["keywords: duplicate rows removed", rows - len(keywords)])

    movie_ids = set(movies["id"])
    summary.append(
        ["credits: ids not in movies (ignored)", len(set(credits["id"]) - movie_ids)]
    )
    summary.append(
        ["keywords: ids not in movies (ignored)", len(set(keywords["id"]) - movie_ids)]
    )
    summary.append(
        ["movies without a credits row", len(movie_ids - set(credits["id"]))]
    )

    cast_by_id = dict(zip(credits["id"], credits["cast"]))
    crew_by_id = dict(zip(credits["id"], credits["crew"]))
    keywords_by_id = dict(zip(keywords["id"], keywords["keywords"]))

    movie_docs = []
    for row in movies.itertuples(index=False):
        collection = None
        if pd.notna(row.belongs_to_collection):
            parsed = ast.literal_eval(row.belongs_to_collection)
            collection = {"id": parsed["id"], "name": parsed["name"]}

        movie_docs.append(
            {
                "_id": int(row.id),
                "imdb_id": to_none(row.imdb_id),
                "title": to_none(row.title),
                "original_title": to_none(row.original_title),
                "original_language": to_none(row.original_language),
                "overview": to_none(row.overview),
                "tagline": to_none(row.tagline),
                "status": to_none(row.status),
                "release_date": to_none(row.release_date),
                "release_year": to_int(row.release_year),
                "runtime": to_int(row.runtime),
                "budget": to_int(row.budget),
                "revenue": to_int(row.revenue),
                "popularity": float(row.popularity),
                "vote_average": (
                    None if pd.isna(row.vote_average) else float(row.vote_average)
                ),
                "vote_count": int(row.vote_count),
                "genres": to_names(row.genres),
                "collection": collection,
                "production_companies": to_names(row.production_companies),
                "production_countries": to_countries(row.production_countries),
                "keywords": to_names(keywords_by_id.get(row.id, "[]")),
                "cast": to_cast(cast_by_id.get(row.id, "[]")),
                "crew": to_crew(crew_by_id.get(row.id, "[]")),
            }
        )

    names_by_id = {}
    for doc in movie_docs:
        for person in doc["cast"] + doc["crew"]:
            names_by_id.setdefault(person["id"], Counter())[person["name"]] += 1

    renamed = 0
    for doc in movie_docs:
        for person in doc["cast"] + doc["crew"]:
            name = names_by_id[person["id"]].most_common(1)[0][0]
            if person["name"] != name:
                person["name"] = name
                renamed += 1
    summary.append(
        [
            "people: ids with several names",
            sum(len(names) > 1 for names in names_by_id.values()),
        ]
    )
    summary.append(["people: names replaced by the most common name", renamed])

    connection.db["movies"].insert_many(movie_docs)
    print("Movies:", len(movie_docs))


def insert_ratings(connection, movies):
    links = pd.read_csv(DATA_DIR / "links.csv").dropna(subset=["tmdbId"])
    tmdb_by_movie = dict(zip(links["movieId"], links["tmdbId"].astype(int)))

    ratings = pd.read_csv(DATA_DIR / "ratings.csv")
    print("Ratings:", len(ratings))

    ratings["movie_id"] = ratings["movieId"].map(tmdb_by_movie)
    missing = ratings["movie_id"].isna()
    unknown = ~missing & ~ratings["movie_id"].isin(movies["id"])
    summary.append(["ratings: dropped, no tmdbId in links.csv", missing.sum()])
    summary.append(["ratings: dropped, tmdbId not in movies", unknown.sum()])
    ratings = ratings[~missing & ~unknown].copy()
    print("Ratings with a movie in movies_metadata:", len(ratings))

    ratings["movie_id"] = ratings["movie_id"].astype(int)
    ratings["timestamp"] = pd.to_datetime(ratings["timestamp"], unit="s")

    rating_rows = len(ratings)
    ratings = ratings.sort_values("timestamp", kind="stable").drop_duplicates(
        ["userId", "movie_id"], keep="last"
    )
    summary.append(
        ["ratings: duplicate (user, movie) removed", rating_rows - len(ratings)]
    )

    genres_by_movie = dict(zip(movies["id"], movies["genres"].map(to_names)))
    users = {}

    rating_docs = []
    rating_count = 0
    for user_id, movie_id, rating, timestamp in zip(
        ratings["userId"], ratings["movie_id"], ratings["rating"], ratings["timestamp"]
    ):
        rating_docs.append(
            {
                "user_id": user_id,
                "movie_id": movie_id,
                "rating": rating,
                "timestamp": timestamp,
            }
        )

        if user_id not in users:
            users[user_id] = {"count": 0, "sum": 0, "sum_squares": 0, "genres": set()}
        user = users[user_id]
        user["count"] += 1
        user["sum"] += rating
        user["sum_squares"] += rating**2
        user["genres"].update(genres_by_movie[movie_id])

        if len(rating_docs) == BATCH_SIZE:
            connection.db["ratings"].insert_many(rating_docs, ordered=False)
            rating_count += len(rating_docs)
            rating_docs = []

            if rating_count % 1000000 == 0:
                print("Ratings inserted:", rating_count)

    if rating_docs:
        connection.db["ratings"].insert_many(rating_docs, ordered=False)
        rating_count += len(rating_docs)
    print("Ratings inserted:", rating_count)
    summary.append(["ratings: inserted", rating_count])

    user_docs = []
    for user_id, user in users.items():
        count = user["count"]
        user_docs.append(
            {
                "_id": user_id,
                "ratings_count": count,
                "rating_sum": user["sum"],
                "rating_sum_squares": user["sum_squares"],
                "rating_variance": (count * user["sum_squares"] - user["sum"] ** 2)
                / count**2,
                "genres": sorted(user["genres"]),
                "genre_count": len(user["genres"]), 
            }
        )
    connection.db["users"].insert_many(user_docs)
    print("Users inserted:", len(user_docs))
    summary.append(["users: inserted", len(user_docs)])


def main():
    connection = DbConnector()
    db = connection.db

    db.drop_collection("movies")
    db.drop_collection("ratings")
    db.drop_collection("users")

    movies = load_movies()
    insert_movies(connection, movies)
    insert_ratings(connection, movies)

    db["movies"].create_index([("overview", "text"), ("tagline", "text")])
    db["movies"].create_index("cast.id")
    db["movies"].create_index("crew.id")
    db["movies"].create_index("release_year")
    db["users"].create_index("ratings_count")

    print("\nCleaning summary")
    print(
        tabulate(
            [[step, int(count)] for step, count in summary], headers=["Step", "Count"]
        )
    )

    connection.close_connection()


if __name__ == "__main__":
    main()
