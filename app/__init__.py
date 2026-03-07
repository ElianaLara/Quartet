from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Global variable for db access
db = None

def create_app():
    global db
    app = Flask(__name__)
    app.config.from_object(Config)

    print(os.environ.get("MONGO_URI"))
    print(os.environ.get("SECRET_KEY"))
    # Connect to MongoDB Atlas
    client = MongoClient(app.config['MONGO_URI'])
    db = client.get_database("mydatabase")  # Uses the database in your URI

    # Register Blueprints
    from .routes import main
    app.register_blueprint(main)
    app.config.from_object(Config)

    return app