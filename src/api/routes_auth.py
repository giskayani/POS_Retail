"""
flask blueprint for authentication endpoints
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from core.database import get_db
from core.id_generator import IDGenerator
from datetime import datetime, timedelta
import jwt
import os

auth_bp = Blueprint("auth_bp", __name__)
SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    db = get_db().db
    user = db.master_karyawan.find_one({"username": username, "status": "active"})

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Invalid username or password"}), 401

    id_gen = IDGenerator(db)
    session_id = id_gen.get_next_id("SES")

    token = jwt.encode({
        "user_id": user["employee_id"],
        "username": username,
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")

    session = {
        "session_id": session_id,
        "user_id": user["employee_id"],
        "username": username,
        "role": user["role"],
        "token": token,
        "issued_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=2),
        "status": "active"
    }

    db.sessions.insert_one(session)
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "employee_id": user["employee_id"],
            "name": user["name"],
            "role": user["role"]
        }
    }), 200

@auth_bp.route("/register", methods=["POST"])
def register():
    from werkzeug.security import generate_password_hash
    
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
    return jsonify({"message": "User registered successfully", "employee_id": employee_id}), 201

@auth_bp.route("/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Authorization header missing"}), 401

    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return jsonify({"error": "Invalid authorization header format"}), 401

    db = get_db().db

    session = db.sessions.find_one({"token": token})
    if not session:
        return jsonify({"error": "Invalid or expired token"}), 401

    if session.get("status") == "inactive":
        return jsonify({"error": "Session already inactive"}), 400

    db.sessions.update_one(
        {"token": token},
        {"$set": {"status": "inactive", "revoked_at": datetime.utcnow()}}
    )

    return jsonify({"message": "Logged out successfully"}), 200
