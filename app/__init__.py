from flask import Flask
from pymongo import MongoClient
from config import Config
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Connect MongoDB
    client = MongoClient(app.config['MONGO_URI'])
    app.db = client["mydatabase"]  # attach db to app object

    from .routes import main
    app.register_blueprint(main)

    return app