from flask import Blueprint, jsonify
from core.database import get_db
from utils.jwt_manager import require_auth
from datetime import datetime, timedelta

dashboard_bp = Blueprint("dashboard_bp", __name__)

@dashboard_bp.route("/stats", methods=["GET"])
@require_auth(role="admin")
def get_dashboard_stats():
    db = get_db().db
    
    # Get today's stats
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    # Today's sales
    today_sales = list(db.transactions.aggregate([
        {"$match": {"created_at": {"$gte": today, "$lt": tomorrow}}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}, "count": {"$sum": 1}}}
    ]))
    
    # Total products
    total_products = db.products.count_documents({"status": "active"})
    
    # Low stock products (stock < 10)
    low_stock = db.products.count_documents({"status": "active", "stock": {"$lt": 10}})
    
    # Total employees
    total_employees = db.master_karyawan.count_documents({"status": "active"})
    
    stats = {
        "today_sales": today_sales[0]["total"] if today_sales else 0,
        "today_transactions": today_sales[0]["count"] if today_sales else 0,
        "total_products": total_products,
        "low_stock_products": low_stock,
        "total_employees": total_employees
    }
    
    return jsonify(stats), 200