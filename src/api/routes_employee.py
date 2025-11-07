from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from core.database import get_db
from core.id_generator import IDGenerator
from utils.jwt_manager import token_required
from datetime import datetime
from functools import wraps

employee_bp = Blueprint("employee", __name__)

@employee_bp.route("/register", methods=["POST"])
def register_employee():
    data = request.get_json()
    required_fields = ["nama", "username", "email", "password", "role"]
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    db = get_db().db
    id_gen = IDGenerator(db)
    
    existing = db.master_karyawan.find_one({
        "$or": [{"username": data["username"]}, {"email": data["email"]}]
    })
    if existing:
        return jsonify({"error": "Username or email already exists"}), 400

    employee_id = id_gen.get_next_id("EMP")
    
    employee = {
        "employee_id": employee_id,
        "name": data["nama"],
        "username": data["username"],
        "email": data["email"],
        "password_hash": generate_password_hash(data["password"]),
        "role": data["role"],
        "status": "active",
        "created_at": datetime.utcnow()
    }

    db.master_karyawan.insert_one(employee)
    return jsonify({"message": "Employee registered successfully", "employee_id": employee_id}), 201

@employee_bp.route("/list", methods=["GET"])
@token_required
def list_employees(current_user):
    db = get_db().db
    employees = list(db.master_karyawan.find(
        {"status": "active"}, 
        {"password_hash": 0}
    ))
    return jsonify(employees), 200

@employee_bp.route("/<employee_id>", methods=["GET"])
@token_required
def get_employee(current_user, employee_id):
    db = get_db().db
    employee = db.master_karyawan.find_one(
        {"employee_id": employee_id}, 
        {"password_hash": 0}
    )
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employee), 200

