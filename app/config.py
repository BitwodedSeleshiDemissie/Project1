import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trip_organizer.db'  # Or use PostgreSQL/MySQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
