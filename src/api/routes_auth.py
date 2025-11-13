"""
flask blueprint for authentication endpoints
"""
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from core.database import get_db
from core.id_generator import IDGenerator
from datetime import datetime, timedelta
from utils.jwt_manager import token_required
import jwt
import os

auth_bp = Blueprint("auth_bp", __name__)
SECRET_KEY = os.getenv("JWT_SECRET", "change_this_secret")

# Di routes_auth.py
@auth_bp.route("/change-my-password", methods=["POST"])
@token_required()
def change_my_password(current_user):
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password or len(new_password) < 8:
        return jsonify({"error": "All field required to fill and new passwprd min 8 character"}), 400

    db = get_db().db
    user_id = current_user["user_id"]
    
    user = db.master_karyawan.find_one({"employee_id": user_id})

    if not user or not check_password_hash(user["password_hash"], current_password):
        return jsonify({"error": "Invalid username or password"}), 401 

    new_password_hash = generate_password_hash(new_password)
    db.master_karyawan.update_one(
        {"employee_id": user_id},
        {"$set": {"password_hash": new_password_hash}}
    )
    
    return jsonify({"message": "Password sucessfully changed"}), 200

@auth_bp.route("/login", methods=["POST"])
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    # SANITASI: REMOVE SPACE AT THE BEGINNING/IN THE LAST SENTENCE
    username = data.get("username", "").strip() 
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    db = get_db().db
    user = db.master_karyawan.find_one({"username": username, "status": "active"}) 

    # ================== BLOK DEBUGGING ==================
    # Tambahkan kode ini untuk melihat apa yang terjadi di terminal Anda
    if user:
        print(f"--- DEBUG: USER DITEMUKAN ---")
        print(f"Username input: '{username}'")
        print(f"Password input: '{password}'")
        print(f"Hash dari DB: '{user.get('password_hash')}'") # Ambil hash dari DB
        
        # Cek manual
        is_valid = check_password_hash(user.get("password_hash", ""), password)
        print(f"Hasil check_password_hash: {is_valid}")
    else:
        print(f"--- DEBUG: USER TIDAK DITEMUKAN ---")
        print(f"Username input: '{username}'")
    # ================== AKHIR BLOK DEBUGGING ==================

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
