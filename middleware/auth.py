import os
import jwt
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

SECRET = os.getenv("JWT_SECRET", "default_secret")

def token_required(f):
    """Vérifie que le token JWT est valide."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"error": "Token manquant"}), 401
        try:
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expiré"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token invalide"}), 401
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    """Vérifie que l'utilisateur a le bon rôle."""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            user_role = request.user.get("role", "")
            if user_role not in roles:
                return jsonify({"error": "Accès refusé — rôle insuffisant"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def generate_token(user_id, email, role, brigade=None):
    import datetime
    payload = {
        "id": str(user_id),
        "email": email,
        "role": role,
        "brigade": brigade,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")
