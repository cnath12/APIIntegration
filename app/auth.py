from flask import request, jsonify, current_app
from functools import wraps

class Auth:
    def __init__(self,app):
        self.app = app

    def require_auth(self, auth_type='any'):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                auth_successful = False
                if auth_type == 'any':
                    auth_successful = self.check_api_key() or self.check_basic_auth()
                elif auth_type == 'api_key':
                    auth_successful = self.check_api_key()
                elif auth_type == 'basic':
                    auth_successful = self.check_basic_auth()
                
                if auth_successful:
                    return f(*args, **kwargs)
                else:
                    return jsonify({"error": "Unauthorized"}), 401
            return decorated_function
        return decorator

    # def check_api_key(self, app):
    #     return request.headers.get('X-API-Key') == app.config['API_KEY']
    def check_api_key(self):
        api_key = request.headers.get('X-API-Key')
        if api_key is None:
            return False
        return api_key == self.app.config['API_KEY']

    def check_basic_auth(self):
        auth = request.authorization
        if not auth:
            return False
        return auth.username == self.app.config['BASIC_AUTH_USERNAME'] and \
               auth.password == self.app.config['BASIC_AUTH_PASSWORD']
        
