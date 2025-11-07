from flask import Blueprint, request, jsonify
from core.database import get_db
from core.id_generator import IDGenerator
from utils.jwt_manager import require_auth
from datetime import datetime, timedelta
import re

sales_bp = Blueprint("sales_bp", __name__)

def validate_transaction_data(data):
    errors = []
    
    if not data.get("items") or not isinstance(data["items"], list):
        errors.append("Items list is required")
        return errors
    
    if len(data["items"]) == 0:
        errors.append("At least one item is required")
    
    for i, item in enumerate(data["items"]):
        if not item.get("product_id"):
            errors.append(f"Item {i+1}: product_id is required")
        
        try:
            qty = int(item.get("quantity", 0))
            if qty <= 0:
                errors.append(f"Item {i+1}: quantity must be positive")
        except (ValueError, TypeError):
            errors.append(f"Item {i+1}: quantity must be a valid number")
    
    if "payment_method" in data and data["payment_method"] not in ["cash", "card", "digital"]:
        errors.append("Invalid payment method")
    
    return errors

@sales_bp.route("/", methods=["POST"])
@require_auth()
def create_transaction():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    errors = validate_transaction_data(data)
    if errors:
        return jsonify({"errors": errors}), 400
    
    db = get_db().db
    id_gen = IDGenerator(db)
    
    # Validate products and calculate total
    transaction_items = []
    total_amount = 0
    
    for item in data["items"]:
        product = db.products.find_one({
            "product_id": item["product_id"],
            "status": "active"
        })
        
        if not product:
            return jsonify({"error": f"Product {item['product_id']} not found"}), 400
        
        quantity = int(item["quantity"])
        
        # Check stock availability
        if product["stock"] < quantity:
            return jsonify({"error": f"Insufficient stock for {product['name']}"}), 400
        
        item_total = product["price"] * quantity
        total_amount += item_total
        
        transaction_items.append({
            "product_id": item["product_id"],
            "product_name": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "subtotal": item_total
        })
    
    # Create transaction
    transaction = {
        "transaction_id": id_gen.get_next_id("TXN"),
        "items": transaction_items,
        "total_amount": total_amount,
        "payment_method": data.get("payment_method", "cash"),
        "cashier_id": request.user["user_id"],
        "cashier_name": request.user.get("username", ""),
        "customer_name": data.get("customer_name", ""),
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    # Update stock for all items
    for item in data["items"]:
        db.products.update_one(
            {"product_id": item["product_id"]},
            {"$inc": {"stock": -int(item["quantity"])}}
        )
    
    result = db.transactions.insert_one(transaction)
    transaction["_id"] = str(result.inserted_id)
    
    return jsonify(transaction), 201

@sales_bp.route("/", methods=["GET"])
@require_auth()
def get_transactions():
    db = get_db().db
    limit = int(request.args.get("limit", 50))
    
    transactions = list(db.transactions.find({}).sort("created_at", -1).limit(limit))
    for t in transactions:
        t["_id"] = str(t["_id"])
    
    return jsonify(transactions), 200

@sales_bp.route("/analytics/daily", methods=["GET"])
@require_auth(role="admin")
def daily_analytics():
    db = get_db().db
    days = int(request.args.get("days", 7))
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "total_sales": {"$sum": "$total_amount"},
                "transaction_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = list(db.transactions.aggregate(pipeline))
    return jsonify(result), 200

@sales_bp.route("/analytics/weekly", methods=["GET"])
@require_auth(role="admin")
def weekly_analytics():
    db = get_db().db
    weeks = int(request.args.get("weeks", 4))
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(weeks=weeks)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": {"$week": "$created_at"},
                "total_sales": {"$sum": "$total_amount"},
                "transaction_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = list(db.transactions.aggregate(pipeline))
    return jsonify(result), 200

@sales_bp.route("/analytics/monthly", methods=["GET"])
@require_auth(role="admin")
def monthly_analytics():
    db = get_db().db
    months = int(request.args.get("months", 6))
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=months*30)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$created_at"}},
                "total_sales": {"$sum": "$total_amount"},
                "transaction_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    result = list(db.transactions.aggregate(pipeline))
    return jsonify(result), 200

@sales_bp.route("/analytics/bestsellers", methods=["GET"])
@require_auth(role="admin")
def bestsellers():
    db = get_db().db
    limit = int(request.args.get("limit", 10))
    
    pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "product_name": {"$first": "$items.product_name"},
                "total_quantity": {"$sum": "$items.quantity"},
                "total_revenue": {"$sum": "$items.subtotal"}
            }
        },
        {"$sort": {"total_quantity": -1}},
        {"$limit": limit}
    ]
    
    result = list(db.transactions.aggregate(pipeline))
    return jsonify(result), 200
