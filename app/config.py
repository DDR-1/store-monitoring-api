import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:Devesh12@localhost:5432/storedb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
