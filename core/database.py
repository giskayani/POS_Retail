"""
MongoDB Connection Helper
"""
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from flask import g

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

_client = None

def get_db():
    if 'db' not in g:
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME")
        
        g.db_client = MongoClient(mongo_uri)
        g.db = g.db_client[db_name]
    return g

