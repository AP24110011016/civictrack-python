"""
Database connection module
Uses PyMongo to connect to MongoDB Atlas
"""
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = None
db = None

def connect_db():
    global client, db
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client['civictrack']
        # Test connection
        client.admin.command('ping')
        print('✅ MongoDB Connected Successfully')
        return db
    except Exception as e:
        print(f'❌ MongoDB Connection Error: {e}')
        raise e

def get_db():
    global db
    if db is None:
        connect_db()
    return db
