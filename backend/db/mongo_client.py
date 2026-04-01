# Written by V
import os
from pymongo import MongoClient
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "devil_has_many_faces"

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def init_mongo():
    db = get_db()
    
    # Create collections with validators
    if "raw_docs" not in db.list_collection_names():
        db.create_collection("raw_docs")
        print("Created collection: raw_docs")

    if "chunks" not in db.list_collection_names():
        db.create_collection("chunks")
        print("Created collection: chunks")

    # Indexes
    db.raw_docs.create_index("doc_id", unique=True)
    db.raw_docs.create_index("corpus")
    db.chunks.create_index("doc_id")
    db.chunks.create_index("corpus")

    print(f"MongoDB initialized. DB: {DB_NAME}")
    print(f"Collections: {db.list_collection_names()}")

if __name__ == "__main__":
    init_mongo()