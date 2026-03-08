from flask import Flask
from config import Config
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Connect MongoDB
    from .routes import main
    client = MongoClient(app.config['MONGO_URI'])
    app.db = client["mydatabase"]  # attach db to app object

    app.register_blueprint(main)

    return app