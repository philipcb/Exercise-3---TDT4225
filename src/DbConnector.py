import os

from dotenv import load_dotenv
from pymongo import MongoClient, version

load_dotenv()


class DbConnector:

    def __init__(self,
                 DATABASE=os.environ.get("MONGO_DB", "movies"),
                 HOST=os.environ.get("MONGO_HOST", "localhost:27017"),
                 USER=os.environ.get("MONGO_USER", "movies_user"),
                 PASSWORD=os.environ.get("MONGO_PASSWORD", "movies123")):
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
