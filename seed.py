# seed.py
import json
from app import create_app
from pymongo import MongoClient

# Initialize Flask app to load config
app = create_app()

# Connect to MongoDB using the URI from config
client = MongoClient(app.config['MONGO_URI'])
db = client.get_database()  # Uses the database in the URI

def seed_collection(collection_name, json_file):
    try:
        collection = db[collection_name]
        with open(json_file, 'r') as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) > 0:
            result = collection.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} documents into '{collection_name}' collection.")
        else:
            print("JSON file is empty or not a list of documents.")
    except FileNotFoundError:
        print(f"File {json_file} not found.")
    except Exception as e:
        print("Error seeding collection:", e)

if __name__ == "__main__":
    seed_collection('user', 'user.json')  # Collection name 'user'