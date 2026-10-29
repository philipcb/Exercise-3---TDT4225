import ast
import pandas as pd
from common import DATA_DIR, load_movies, save_table


def analyze_credits(credits):
    cast_sizes = []
    directors = []
    gender_counts = {0: 0, 1: 0, 2: 0}
    for cast, crew in zip(credits["cast"], credits["crew"]):
        cast = ast.literal_eval(cast)
        cast_sizes.append(len(cast))
        for member in cast:
            gender_counts[member["gender"]] += 1

        director_count = 0
        for member in ast.literal_eval(crew):
            if member["job"] == "Director":
                director_count += 1
        directors.append(director_count)

    stats = pd.Series(cast_sizes).describe().round(2)
    save_table(stats.items(), "people", "cast_size.csv", ["Statistic", "Cast size"])

    director_counts = pd.Series(directors).clip(upper=3).value_counts().sort_index()
    save_table(director_counts.items
               (), "people", "directors_per_movie.csv", ["Directors (3 = 3+)", "Movies"])

    rows = [["Unknown (0)", gender_counts[0]], ["Female (1)", gender_counts[1]], ["Male (2)", gender_counts[2]]]
    save_table(rows, "people", "cast_gender.csv", ["Gender", "Cast members"])


def analyze_repeated_people(casts, crews):
    repeated_cast = 0
    repeated_directors = 0
    for cast, crew in zip(casts, crews):
        cast_ids = []
        for member in cast:
            cast_ids.append(member["id"])
        repeated_cast += len(cast_ids) != len(set(cast_ids))

        director_ids = []
        for member in crew:
            if member["job"] == "Director":
                director_ids.append(member["id"])
        repeated_directors += len(director_ids) != len(set(director_ids))

    summary = [
        ["Movies with the same person id more than once in cast", repeated_cast],
        ["Movies with the same Director id more than once in crew", repeated_directors],
    ]
    save_table(summary, "people", "repeated_people.csv", ["Measure", "Movies"])


def analyze_cast_order(casts):
    fewer_than_5 = 0
    repeated_order = 0
    for cast in casts:
        orders = []
        for member in cast:
            orders.append(member["order"])
        fewer_than_5 += len(cast) < 5
        repeated_order += len(orders) != len(set(orders))

    summary = [
        ["Movies with fewer than 5 cast members", fewer_than_5],
        ["Movies with repeated order values in cast", repeated_order],
    ]
    save_table(summary, "people", "cast_order.csv", ["Measure", "Movies"])


def analyze_person_identity(casts, crews):
    names_per_id = {}
    ids_per_name = {}
    director_jobs = {}
    for cast, crew in zip(casts, crews):
        for member in cast + crew:
            names_per_id.setdefault(member["id"], set()).add(member["name"])
            ids_per_name.setdefault(member["name"], set()).add(member["id"])
        for member in crew:
            if "director" in member["job"].lower():
                director_jobs[member["job"]] = director_jobs.get(member["job"], 0) + 1

    ids_with_several_names = 0
    for names in names_per_id.values():
        ids_with_several_names += len(names) > 1
    names_with_several_ids = 0
    for ids in ids_per_name.values():
        names_with_several_ids += len(ids) > 1

    summary = [
        ["Person ids with several names", ids_with_several_names],
        ["Names with several person ids", names_with_several_ids],
    ]
    save_table(summary, "people", "person_identity.csv", ["Measure", "Count"])

    # Shows if other spellings of Director exist that job == "Director" would miss
    rows = sorted(director_jobs.items(), key=lambda item: -item[1])
    save_table(rows, "people", "director_jobs.csv", ["Job", "Crew entries"])


def main():
    credits = pd.read_csv(DATA_DIR / "credits.csv").drop_duplicates("id")
    analyze_credits(credits)

    # Same cleaning as insert_data.py, so only movies that are inserted are counted
    movies = load_movies().drop_duplicates("id")
    credits = credits[credits["id"].isin(movies["id"])]
    casts = credits["cast"].map(ast.literal_eval)
    crews = credits["crew"].map(ast.literal_eval)
    analyze_repeated_people(casts, crews)
    analyze_cast_order(casts)
    analyze_person_identity(casts, crews)


if __name__ == '__main__':
    main()
