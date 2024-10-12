# app/rbac/utils.py

from functools import wraps
from flask import jsonify, g
from .constants import ROLES

def rbac_required(required_permissions):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user or not g.user.roles:
                return jsonify({"error": "Unauthorized"}), 401
            
            user_permissions = set()
            for role in g.user.roles:
                user_permissions.update(ROLES.get(role, []))
            
            if not set(required_permissions).issubset(user_permissions):
                return jsonify({"error": "Forbidden"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator