from flask import request, jsonify, current_app
from functools import wraps

class Auth:
    def __init__(self,app):
        self.app = app

    def require_auth(self, auth_type='any'):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                app = self.app or current_app
                
                if auth_type == 'any':
                    if self.check_api_key(app) or self.check_basic_auth(app):
                        return f(*args, **kwargs)
                elif auth_type == 'api_key' and self.check_api_key(app):
                    return f(*args, **kwargs)
                elif auth_type == 'basic' and self.check_basic_auth(app):
                    return f(*args, **kwargs)
                else:
                    app.logger.warning("Unauthorized access attempt")
                    return jsonify({"error": "Unauthorized"}), 401
            return decorated_function
        return decorator

    def check_api_key(self, app):
        return request.headers.get('X-API-Key') == app.config['API_KEY']

    def check_basic_auth(self, app):
        auth = request.authorization
        if not auth:
            return False
        return auth.username == app.config['BASIC_AUTH_USERNAME'] and \
               auth.password == app.config['BASIC_AUTH_PASSWORD']
