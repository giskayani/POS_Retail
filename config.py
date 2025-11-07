"""
simple configuration (env-backed)
"""
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://672023205:100905@kapita-selekta.1dalocx.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "smart_retail_db")
SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret")
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", "2"))

# # AUTH DB
# MONGODB_AUTHDATABASE = "auth_db"
# MONGODB_COLLECTION_USER = "users"
# MONGO_COLLECTION_SESSION = "sessions"
