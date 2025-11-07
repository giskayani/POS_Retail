"""
services/session_service.py
JWT Session Management
"""
import jwt
import os
from datetime import datetime, timedelta
from core.database import get_db
from core.id_generator import generate_id

SECRET_KEY = os.getenv("SECRET_KEY", "change_this_secret")
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", 2))

def create_session(user):
    db = get_db()
    session_id = generate_id("SES")

    token = jwt.encode({
        "user_id": user["employee_id"],
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXP_HOURS)
    }, SECRET_KEY, algorithm="HS256")

    session_data = {
        "session_id": session_id,
        "user_id": user["employee_id"],
        "username": user["username"],
        "role": user["role"],
        "token": token,
        "issued_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=JWT_EXP_HOURS),
        "status": "active"
    }

    db.sessions.insert_one(session_data)
    return token, session_id

def verify_token(token):
    db = get_db()
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None  # expired token
    except jwt.InvalidTokenError:
        return None  # broken/wrong token

    session = db.sessions.find_one({"token": token})
    if not session or session.get("status") != "active":
        return None  # inactive token (logout)

    return decoded

def destroy_session(token):
    db = get_db()
    result = db.sessions.update_one(
        {"token": token},
        {"$set": {"status": "inactive", "revoked_at": datetime.utcnow()}}
    )
    return result.modified_count > 0


