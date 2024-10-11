from flask import request, jsonify, current_app
from functools import wraps

class Auth:
    def __init__(self, app, jwt_auth, oauth_auth, api_key_auth):
        self.app = app
        self.jwt_auth = jwt_auth
        self.oauth_auth = oauth_auth
        self.api_key_auth = api_key_auth

    def require_auth(self, auth_type='any'):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                auth_successful = False
                print(f"Checking auth type: {auth_type}")
                if auth_type == 'any':
                    auth_successful = (self.    api_key_auth.check_api_key() or 
                                       self.check_basic_auth() or 
                                       self.jwt_auth.check_jwt())
                elif auth_type == 'api_key':
                    auth_successful = self.api_key_auth.check_api_key()
                elif auth_type == 'basic':
                    auth_successful = self.check_basic_auth()
                elif auth_type == 'jwt':
                    return self.jwt_auth.jwt_required()(f)(*args, **kwargs)
                print(f"Auth successful: {auth_successful}")
                if auth_successful:
                    return f(*args, **kwargs)
                else:
                    return jsonify({"error": "Unauthorized"}), 401
            return decorated_function
        return decorator

    def check_basic_auth(self):
        auth = request.authorization
        if not auth:
            current_app.logger.info("No authorization header found")
            return False
        result = auth.username == self.app.config['BASIC_AUTH_USERNAME'] and \
                 auth.password == self.app.config['BASIC_AUTH_PASSWORD']
        return result