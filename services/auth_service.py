"""
Auth business logic: register and login.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from core.database import get_db
from utils.jwt_manager import generate_token

_users = get_db().users
# ensure index on username for uniqueness
try:
    _users.create_index("username", unique=True)
except Exception:
    pass

def register_user(username: str, password: str, role: str = "kasir"):
    """
    Register a new user. Returns inserted id (str) or None if exists.
    """
    if _users.find_one({"username": username}):
        return None
    hashed = generate_password_hash(password)
    res = _users.insert_one({"username": username, "password": hashed, "role": role})
    return str(res.inserted_id)

def authenticate_user(username: str, password: str):
    """
    Verify credentials and return token info dict or None.
    """
    user = _users.find_one({"username": username})
    if not user:
        return None
    if not check_password_hash(user["password"], password):
        return None
    token = generate_token(str(user["_id"]), user.get("role", "kasir"))
    return {"token": token, "user_id": str(user["_id"]), "role": user.get("role")}
