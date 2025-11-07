"""
services/karyawan_service.py
Manage employee (karyawan) data.
"""
from werkzeug.security import generate_password_hash
from core.database import get_db
from core.id_generator import IDGenerator
from datetime import datetime

db = get_db().db
id_gen = IDGenerator(db)

def create_karyawan(name, username, password, role):
    # Generate unique employee ID
    emp_id = id_gen.get_next_id("EMP")
    password_hash = generate_password_hash(password)

    karyawan = {
        "employee_id": emp_id,
        "name": name,
        "username": username,
        "password_hash": password_hash,
        "role": role,
        "status": "active",
        "created_at": datetime.utcnow()
    }

    db.master_karyawan.insert_one(karyawan)
    return emp_id
