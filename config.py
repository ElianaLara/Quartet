import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    MONGO_URI = os.environ.get('MONGO_URI')