import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = None
db = None

def get_db():
    global client, db
    if db is None:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI manquant dans .env")
        client = MongoClient(mongo_uri)
        db = client["snde_incidents"]
        print("Connexion MongoDB établie")
    return db
