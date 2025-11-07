"""
Seed foundational collections, counters, and default data for Smart Retail DB.
Safe to run multiple times (idempotent).
"""
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

# ---------- UTILITIES ----------
def reset_counter_if_empty(collection_name: str, counter_id: str):
    """Reset counter if related collection is empty."""
    if db[collection_name].count_documents({}) == 0:
        db.counters.update_one(
            {"_id": counter_id},
            {"$set": {"sequence_value": 0}},
            upsert=True
        )
        print(f"Counter '{counter_id}' reset to 0 (collection empty).")
    else:
        # Ensure counter exists even if not reset
        db.counters.update_one(
            {"_id": counter_id},
            {"$setOnInsert": {"sequence_value": 0}},
            upsert=True
        )

def get_next_sequence(name):
    """Generate next sequence value for given counter name."""
    counter = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"sequence_value": 1}},
        return_document=True,
        upsert=True
    )
    return counter["sequence_value"]

# ---------- SEED FUNCTIONS ----------
def seed_default_collections():
    for collection in ["products", "sales", "users", "counters"]:
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            print(f"Created collection: {collection}")

def seed_admin_user():
    if db.users.count_documents({"username": "admin"}) == 0:
        admin = {
            "user_id": f"U{get_next_sequence('user_id'):04d}",
            "username": "admin",
            "password_hash": generate_password_hash("admin123"),
            "role": "admin"
        }
        db.users.insert_one(admin)
        print("Admin user created.")
    else:
        print("Admin user already exists.")

def seed_counters():
    counters = ["product_id", "variant_id", "sale_id", "user_id"]
    for c in counters:
        db.counters.update_one(
            {"_id": c},
            {"$setOnInsert": {"sequence_value": 0}},
            upsert=True
        )
    print("Counters initialized.")

def seed_sample_products():
    if db.products.count_documents({}) == 0:
        sample_products = [
            {
                "product_id": f"P{get_next_sequence('product_id'):04d}",
                "name": "Kopi Tubruk Premium",
                "price": 25000,
                "stock": 120,
                "variants": [
                    {"variant_id": f"V{get_next_sequence('variant_id'):04d}", "name": "250g", "price": 25000},
                    {"variant_id": f"V{get_next_sequence('variant_id'):04d}", "name": "500g", "price": 45000}
                ]
            },
            {
                "product_id": f"P{get_next_sequence('product_id'):04d}",
                "name": "Teh Hijau Organik",
                "price": 20000,
                "stock": 90,
                "variants": [
                    {"variant_id": f"V{get_next_sequence('variant_id'):04d}", "name": "100g", "price": 20000},
                    {"variant_id": f"V{get_next_sequence('variant_id'):04d}", "name": "200g", "price": 35000}
                ]
            }
        ]
        db.products.insert_many(sample_products)
        print("Sample products inserted.")
    else:
        print("Products already exist.")

# ---------- MAIN EXECUTION ----------
if __name__ == "__main__":
    seed_default_collections()
    seed_counters()
    seed_admin_user()
    seed_sample_products()

    # Reset counters only if collections are empty
    reset_counter_if_empty("products", "product_id")
    reset_counter_if_empty("sales", "sale_id")
    reset_counter_if_empty("users", "user_id")
    reset_counter_if_empty("products", "variant_id")

    print("Database seeding complete.")
