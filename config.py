import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dolphin-assessment-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///assessment.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
