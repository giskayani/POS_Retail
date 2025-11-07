from flask import Blueprint, request, jsonify
from core.database import get_db
from core.id_generator import IDGenerator
from utils.jwt_manager import require_auth
from datetime import datetime
import re

product_bp = Blueprint("product_bp", __name__)

def validate_product_data(data, required_fields=None):
    if required_fields is None:
        required_fields = ['name', 'price', 'stock']
    
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field} is required")
    
    if 'price' in data and data['price']:
        try:
            price = float(data['price'])
            if price < 0:
                errors.append("Price must be positive")
        except ValueError:
            errors.append("Price must be a valid number")
    
    if 'stock' in data and data['stock']:
        try:
            stock = int(data['stock'])
            if stock < 0:
                errors.append("Stock must be non-negative")
        except ValueError:
            errors.append("Stock must be a valid integer")
    
    if 'name' in data and data['name']:
        if len(data['name'].strip()) < 2:
            errors.append("Product name must be at least 2 characters")
    
    return errors

@product_bp.route("/", methods=["GET"])
@require_auth()
def get_products():
    db = get_db().db
    products = list(db.products.find({"status": {"$ne": "deleted"}}))
    for p in products:
        p["_id"] = str(p["_id"])
    return jsonify(products), 200

@product_bp.route("/", methods=["POST"])
@require_auth(role="admin")
def create_product():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    errors = validate_product_data(data)
    if errors:
        return jsonify({"errors": errors}), 400
    
    db = get_db().db
    id_gen = IDGenerator(db)
    
    # Check duplicate name
    existing = db.products.find_one({"name": data["name"], "status": {"$ne": "deleted"}})
    if existing:
        return jsonify({"error": "Product name already exists"}), 400
    
    product = {
        "product_id": id_gen.get_next_id("PRD"),
        "name": data["name"].strip(),
        "category": data.get("category", "").strip(),
        "price": float(data["price"]),
        "stock": int(data["stock"]),
        "sku": data.get("sku", "").strip(),
        "status": "active",
        "created_at": datetime.utcnow()
    }
    
    result = db.products.insert_one(product)
    product["_id"] = str(result.inserted_id)
    return jsonify(product), 201

@product_bp.route("/<product_id>", methods=["PUT"])
@require_auth(role="admin")
def update_product(product_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    errors = validate_product_data(data, required_fields=[])
    if errors:
        return jsonify({"errors": errors}), 400
    
    db = get_db().db
    
    # Check if product exists
    existing = db.products.find_one({"product_id": product_id, "status": {"$ne": "deleted"}})
    if not existing:
        return jsonify({"error": "Product not found"}), 404
    
    # Check duplicate name if name is being updated
    if "name" in data:
        duplicate = db.products.find_one({
            "name": data["name"],
            "product_id": {"$ne": product_id},
            "status": {"$ne": "deleted"}
        })
        if duplicate:
            return jsonify({"error": "Product name already exists"}), 400
    
    update_data = {"updated_at": datetime.utcnow()}
    for field in ["name", "category", "price", "stock", "sku"]:
        if field in data:
            if field in ["price"]:
                update_data[field] = float(data[field])
            elif field in ["stock"]:
                update_data[field] = int(data[field])
            else:
                update_data[field] = data[field].strip() if isinstance(data[field], str) else data[field]
    
    db.products.update_one({"product_id": product_id}, {"$set": update_data})
    return jsonify({"message": "Product updated successfully"}), 200

@product_bp.route("/<product_id>", methods=["DELETE"])
@require_auth(role="admin")
def delete_product(product_id):
    db = get_db().db
    
    result = db.products.update_one(
        {"product_id": product_id, "status": {"$ne": "deleted"}},
        {"$set": {"status": "deleted", "deleted_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify({"message": "Product deleted successfully"}), 200
