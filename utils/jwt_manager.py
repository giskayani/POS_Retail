"""
JWT helper and decorator for route protection.
"""
from functools import wraps
from flask import request, jsonify
import jwt
from config import SECRET_KEY, JWT_EXP_HOURS
import datetime

def generate_token(user_id: str, role: str) -> str:
    """
    Create JWT token with user_id and role, expires in JWT_EXP_HOURS.
    """
    payload = {
        "user_id": str(user_id),
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXP_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token: str):
    """
    Decode token and return payload. Raises jwt exceptions on failure.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

def require_auth(role: str = None):
    """
    Decorator to require Authorization: Bearer <token>.
    If role provided, checks payload['role'] == role or payload['role']=='admin'.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error":"missing token"}), 401
            token = auth.split(" ", 1)[1]
            try:
                payload = decode_token(token)
            except Exception as e:
                return jsonify({"error":"invalid or expired token", "detail": str(e)}), 401
            # role check
            if role and payload.get("role") != role and payload.get("role") != "admin":
                return jsonify({"error":"forbidden"}), 403
            # attach user info to request (optional)
            request.user = payload
            return f(*args, **kwargs)
        return wrapped
    return decorator

# token_required: backward-compatible decorator
def token_required(role=None):
    """
    Can be used as:
    @token_required
    def f(current_user, ...)

    or
    @token_required()
    @token_required("manager")
    """
    # If used directly as @token_required without parentheses
    if callable(role):
        func = role
        role = None
        @wraps(func)
        def wrapped_no_args(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error":"missing token"}), 401
            token = auth.split(" ", 1)[1]
            try:
                payload = decode_token(token)
            except Exception as e:
                return jsonify({"error":"invalid or expired token", "detail": str(e)}), 401
            if role and payload.get("role") != role and payload.get("role") != "admin":
                return jsonify({"error":"forbidden"}), 403
            # pass payload as current_user to the route
            return func(payload, *args, **kwargs)
        return wrapped_no_args

    # If used as @token_required() or @token_required("role")
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error":"missing token"}), 401
            token = auth.split(" ", 1)[1]
            try:
                payload = decode_token(token)
            except Exception as e:
                return jsonify({"error":"invalid or expired token", "detail": str(e)}), 401
            if role and payload.get("role") != role and payload.get("role") != "admin":
                return jsonify({"error":"forbidden"}), 403
            return func(payload, *args, **kwargs)
        return wrapped
    return decorator
