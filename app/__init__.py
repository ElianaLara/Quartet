from flask import Flask
from config import Config
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    client = MongoClient(app.config['MONGO_URI'])

    # store db inside app
    app.db = client.get_database("mydatabase")

    from .routes import main
    app.register_blueprint(main)

    return app