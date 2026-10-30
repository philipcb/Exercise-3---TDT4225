from pathlib import Path
import pandas as pd
from DbConnector import DbConnector

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "query_results"
YEAR = {"$year": "$release_date"}
DECADE = {"$subtract": [YEAR, {"$mod": [YEAR, 10]}]}


class Queries:

    def __init__(self):
        self.connection = DbConnector()
        self.db = self.connection.db

    def save_table(self, rows, name, columns=None):
        RESULTS_DIR.mkdir(exist_ok=True)
        pd.DataFrame(rows, columns=columns).round(2).to_csv(
            RESULTS_DIR / name, index=False
        )

    def run_query(self, collection, pipeline, name):
        rows = list(self.db[collection].aggregate(pipeline, allowDiskUse=True))
        self.save_table(rows, name)
        return rows

    def task_1_top_directors_by_median_revenue(self):
        pipeline = [
            {"$unwind": "$crew"},
            {"$match": {"crew.job": "Director"}},
            {
                "$group": {
                    "_id": "$crew.id",
                    "director": {"$first": "$crew.name"},
                    "movie_count": {"$sum": 1},
                    "median_revenue": {
                        "$median": {"input": "$revenue", "method": "approximate"}
                    },
                    "mean_vote_average": {"$avg": "$vote_average"},
                }
            },
            {"$match": {"movie_count": {"$gte": 5}}},
            {"$sort": {"median_revenue": -1}},
            {"$limit": 10},
            {"$project": {"_id": 0}},
        ]
        self.run_query("movies", pipeline, "task_1.csv")

    def task_2_actor_pairs(self):
        pipeline = [
            {"$project": {"actor_1": "$cast", "actor_2": "$cast", "vote_average": 1}},
            {"$unwind": "$actor_1"},
            {"$unwind": "$actor_2"},
            {"$match": {"$expr": {"$lt": ["$actor_1.id", "$actor_2.id"]}}},
            {
                "$group": {
                    "_id": {"actor_1": "$actor_1.id", "actor_2": "$actor_2.id"},
                    "actor_1": {"$first": "$actor_1.name"},
                    "actor_2": {"$first": "$actor_2.name"},
                    "co_appearances": {"$sum": 1},
                    "avg_vote_average": {"$avg": "$vote_average"},
                }
            },
            {"$match": {"co_appearances": {"$gte": 3}}},
            {"$sort": {"co_appearances": -1, "avg_vote_average": -1}},
            {"$limit": 20},
            {"$project": {"_id": 0}},
        ]
        self.run_query("movies", pipeline, "task_2.csv")

    def task_3_actors_genre_breadth(self):
        pipeline = [
            {"$unwind": "$cast"},
            {
                "$group": {
                    "_id": "$cast.id",
                    "actor": {"$first": "$cast.name"},
                    "movie_count": {"$sum": 1},
                    "genre_lists": {"$push": "$genres"},
                }
            },
            {"$match": {"movie_count": {"$gte": 10}}},
            {
                "$project": {
                    "_id": 0,
                    "actor": 1,
                    "movie_count": 1,
                    "genres": {
                        "$reduce": {
                            "input": "$genre_lists",
                            "initialValue": [],
                            "in": {"$setUnion": ["$$value", "$$this"]},
                        }
                    },
                }
            },
            {
                "$project": {
                    "actor": 1,
                    "movie_count": 1,
                    "genre_count": {"$size": "$genres"},
                    "example_genres": {"$slice": ["$genres", 5]},
                }
            },
            {"$sort": {"genre_count": -1, "movie_count": -1}},
            {"$limit": 10},
        ]
        self.run_query("movies", pipeline, "task_3.csv")

    def task_4_top_collections_by_revenue(self):
        pipeline = [
            {"$match": {"collection": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$collection.id",
                    "collection": {"$first": "$collection.name"},
                    "movie_count": {"$sum": 1},
                    "total_revenue": {"$sum": "$revenue"},
                    "median_vote_average": {
                        "$median": {"input": "$vote_average", "method": "approximate"}
                    },
                    "earliest_release": {"$min": "$release_date"},
                    "latest_release": {"$max": "$release_date"},
                }
            },
            {"$match": {"movie_count": {"$gte": 3}}},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 10},
            {"$project": {"_id": 0}},
        ]
        self.run_query("movies", pipeline, "task_4.csv")

    def task_5_runtime_by_decade_and_genre(self):
        pipeline = [
            {"$match": {"release_date": {"$ne": None}, "genres.0": {"$exists": True}}},
            {
                "$group": {
                    "_id": {"decade": DECADE, "primary_genre": {"$first": "$genres"}},
                    "median_runtime": {
                        "$median": {"input": "$runtime", "method": "approximate"}
                    },
                    "movie_count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.decade": 1, "median_runtime": -1}},
            {
                "$project": {
                    "_id": 0,
                    "decade": "$_id.decade",
                    "primary_genre": "$_id.primary_genre",
                    "median_runtime": "$median_runtime",
                    "movie_count": "$movie_count",
                }
            },
        ]
        self.run_query("movies", pipeline, "task_5.csv")

    def task_6_female_share_top_5_cast(self):
        pipeline = [
            {"$match": {"release_date": {"$ne": None}}},
            {
                "$project": {
                    "decade": DECADE,
                    "top_5": {
                        "$slice": [
                            {"$sortArray": {"input": "$cast", "sortBy": {"rank": 1}}},
                            5,
                        ]
                    },
                }
            },
            {
                "$project": {
                    "decade": 1,
                    "genders": {
                        "$filter": {
                            "input": "$top_5.gender",
                            "cond": {"$ne": ["$$this", None]},
                        }
                    },
                }
            },
            {"$match": {"genders.0": {"$exists": True}}},
            {
                "$project": {
                    "decade": 1,
                    "female_share": {
                        "$divide": [
                            {
                                "$size": {
                                    "$filter": {
                                        "input": "$genders",
                                        "cond": {"$eq": ["$$this", 1]},
                                    }
                                }
                            },
                            {"$size": "$genders"},
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": "$decade",
                    "avg_female_share": {"$avg": "$female_share"},
                    "movie_count": {"$sum": 1},
                }
            },
            {"$sort": {"avg_female_share": -1}},
            {
                "$project": {
                    "_id": 0,
                    "decade": "$_id",
                    "avg_female_share": "$avg_female_share",
                    "movie_count": "$movie_count",
                }
            },
        ]
        self.run_query("movies", pipeline, "task_6.csv")

    def task_7_noir_movies(self):
        pipeline = [
            # The text index splits "neo-noir" into "neo" and "noir", so searching for "noir" also finds neo-noir
            {"$match": {"$text": {"$search": "noir"}, "vote_count": {"$gte": 50}}},
            {"$sort": {"vote_average": -1, "vote_count": -1}},
            {"$limit": 20},
            {
                "$project": {
                    "_id": 0,
                    "title": "$title",
                    "year": YEAR,
                    "vote_average": "$vote_average",
                    "vote_count": "$vote_count",
                }
            },
        ]
        self.run_query("movies", pipeline, "task_7.csv")

    def task_8_director_actor_pairs(self):
        pipeline = [
            {"$match": {"vote_count": {"$gte": 100}}},
            {
                "$project": {
                    "directors": {
                        "$filter": {
                            "input": "$crew",
                            "cond": {"$eq": ["$$this.job", "Director"]},
                        }
                    },
                    "cast": 1,
                    "vote_average": 1,
                    "revenue": 1,
                }
            },
            {"$unwind": "$directors"},
            {"$unwind": "$cast"},
            # A director acting in their own movie is not a pair
            {"$match": {"$expr": {"$ne": ["$directors.id", "$cast.id"]}}},
            {
                "$group": {
                    "_id": {"director": "$directors.id", "actor": "$cast.id"},
                    "director": {"$first": "$directors.name"},
                    "actor": {"$first": "$cast.name"},
                    "film_count": {"$sum": 1},
                    "mean_vote_average": {"$avg": "$vote_average"},
                    "mean_revenue": {"$avg": "$revenue"},
                }
            },
            {"$match": {"film_count": {"$gte": 3}}},
            {"$sort": {"mean_vote_average": -1, "film_count": -1}},
            {"$limit": 20},
            {"$project": {"_id": 0}},
        ]
        self.run_query("movies", pipeline, "task_8.csv")

    def task_9_non_english_us_movies(self):
        pipeline = [
            {
                "$match": {
                    "original_language": {"$nin": ["en", None]},
                    "production_countries.iso_3166_1": "US",
                }
            },
            {
                "$group": {
                    "_id": "$original_language",
                    "movie_count": {"$sum": 1},
                    "example_title": {"$first": "$title"},
                }
            },
            {"$sort": {"movie_count": -1}},
            {"$limit": 10},
            {
                "$project": {
                    "_id": 0,
                    "original_language": "$_id",
                    "movie_count": "$movie_count",
                    "example_title": "$example_title",
                }
            },
        ]
        self.run_query("movies", pipeline, "task_9.csv")

    def task_10_user_genre_diversity_and_variance(self):
        project = {
            "_id": 0,
            "user_id": "$_id",
            "ratings_count": "$ratings_count",
            "rating_variance": "$rating_variance",
            "distinct_genres": "$genre_count",
        }
        pipeline = [
            {"$match": {"ratings_count": {"$gte": 20}}},
            {"$sort": {"genre_count": -1, "ratings_count": -1, "_id": 1}},
            {"$limit": 10},
            {"$project": project},
        ]
        self.run_query("users", pipeline, "task_10_genre_diverse_users.csv")

        pipeline = [
            {"$match": {"ratings_count": {"$gte": 20}}},
            {"$sort": {"rating_variance": -1, "ratings_count": -1, "_id": 1}},
            {"$limit": 10},
            {"$project": project},
        ]
        self.run_query("users", pipeline, "task_10_highest_variance_users.csv")


def main():
    program = Queries()

    program.task_1_top_directors_by_median_revenue()
    program.task_2_actor_pairs()
    program.task_3_actors_genre_breadth()
    program.task_4_top_collections_by_revenue()
    program.task_5_runtime_by_decade_and_genre()
    program.task_6_female_share_top_5_cast()
    program.task_7_noir_movies()
    program.task_8_director_actor_pairs()
    program.task_9_non_english_us_movies()
    program.task_10_user_genre_diversity_and_variance()
    program.connection.close_connection()


if __name__ == "__main__":
    main()
