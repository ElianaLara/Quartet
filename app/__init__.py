from flask import Flask
from config import Config
from pymongo import MongoClient

# Global variable for db access
db = None

def create_app():
    global db
    app = Flask(__name__)
    app.config.from_object(Config)

    # Connect to MongoDB Atlas
    client = MongoClient(app.config['MONGO_URI'])
    db = client.get_database()  # Uses the database in your URI

    # Register Blueprints
    from .routes import main
    app.register_blueprint(main)

    return app