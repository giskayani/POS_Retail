from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
# TAMBAHKAN INI
print("--- [DEBUG SEEDER] ---")
print(f"MONGO_URI: {os.getenv('MONGO_URI')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print("-----------------------")

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

def get_next_sequence(name):
    counter = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"sequence_value": 1}},
        return_document=True,
        upsert=True
    )
    return counter["sequence_value"]

def seed_collections():
    collections = ["master_karyawan", "products", "sales", "sessions", "counters"]
    for collection in collections:
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            print(f"Created collection: {collection}")

def seed_counters():
    counters = ["EMP", "PRD", "TXN", "SES"]
    for c in counters:
        db.counters.update_one(
            {"_id": c},
            {"$setOnInsert": {"sequence_value": 0}},
            upsert=True
        )
    print("Counters initialized.")

def seed_employees():
    if db.master_karyawan.count_documents({"username": "admin"}) == 0:
        employees = [
            {
                "employee_id": f"EMP{get_next_sequence('EMP'):04d}",
                "name": "Administrator",
                "username": "admin",
                "email": "admin@smartretail.com",
                "password_hash": generate_password_hash("admin123"),
                "role": "admin",
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "employee_id": f"EMP{get_next_sequence('EMP'):04d}",
                "name": "Kasir 1",
                "username": "kasir1",
                "email": "kasir1@smartretail.com",
                "password_hash": generate_password_hash("kasir123"),
                "role": "kasir",
                "status": "active",
                "created_at": datetime.utcnow()
            }
        ]
        db.master_karyawan.insert_many(employees)
        print("Default employees created.")
    else:
        print("Employees already exist.")

def seed_products():
    if db.products.count_documents({}) == 0:
        products = [
            {
                "product_id": f"PRD{get_next_sequence('PRD'):04d}",
                "name": "Kopi Arabica Premium",
                "category": "Beverages",
                "price": 25000,
                "stock": 50,
                "sku": "KAP001",
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "product_id": f"PRD{get_next_sequence('PRD'):04d}",
                "name": "Teh Hijau Organik",
                "category": "Beverages",
                "price": 20000,
                "stock": 30,
                "sku": "THO001",
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "product_id": f"PRD{get_next_sequence('PRD'):04d}",
                "name": "Roti Bakar Coklat",
                "category": "Food",
                "price": 15000,
                "stock": 25,
                "sku": "RBC001",
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "product_id": f"PRD{get_next_sequence('PRD'):04d}",
                "name": "Sandwich Tuna",
                "category": "Food",
                "price": 18000,
                "stock": 20,
                "sku": "ST001",
                "status": "active",
                "created_at": datetime.utcnow()
            },
            {
                "product_id": f"PRD{get_next_sequence('PRD'):04d}",
                "name": "Jus Jeruk Segar",
                "category": "Beverages",
                "price": 12000,
                "stock": 40,
                "sku": "JJS001",
                "status": "active",
                "created_at": datetime.utcnow()
            }
        ]
        db.products.insert_many(products)
        print("Sample products created.")
    else:
        print("Products already exist.")

if __name__ == "__main__":
    print("Starting database seeding...")
    seed_collections()
    seed_counters()
    seed_employees()
    seed_products()
    print("Database seeding complete.")
    print("\nDefault login credentials:")
    print("Admin - Username: admin, Password: admin123")
    print("Kasir - Username: kasir1, Password: kasir123")