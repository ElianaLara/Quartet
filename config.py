import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    MONGO_URI = "mongodb+srv://eliana_lara:Elia0205@quartet.rozebiq.mongodb.net/mydatabase?retryWrites=true&w=majority"