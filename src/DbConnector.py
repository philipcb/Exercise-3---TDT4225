import os

from dotenv import load_dotenv
from pymongo import MongoClient, version

load_dotenv()


def read_env(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError("%s is missing. Copy .env.example to .env and fill in the values." % name)
    return value


class DbConnector:

    def __init__(self, DATABASE=None, HOST=None, USER=None, PASSWORD=None):
        # The connection settings are only read from .env, so no password is stored in the code
        DATABASE = DATABASE or read_env("MONGO_DB")
        HOST = HOST or read_env("MONGO_HOST")
        USER = USER or read_env("MONGO_USER")
        PASSWORD = PASSWORD or read_env("MONGO_PASSWORD")
        uri = "mongodb://%s:%s@%s/%s" % (USER, PASSWORD, HOST, DATABASE)
        # Connect to the databases
        try:
            self.client = MongoClient(uri)
            self.db = self.client[DATABASE]
        except Exception as e:
            print("ERROR: Failed to connect to db:", e)

        # get database information
        print("You are connected to the database:", self.db.name)
        print("-----------------------------------------------\n")

    def close_connection(self):
        # close the cursor
        # close the DB connection
        self.client.close()
        print("\n-----------------------------------------------")
        print("Connection to %s-db is closed" % self.db.name)
