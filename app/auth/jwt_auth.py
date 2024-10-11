from flask import jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

class JWTAuth:
    def __init__(self, app):
        self.jwt = JWTManager(app)

    def jwt_required(self):
        return jwt_required()

    def check_jwt(self):
        try:
            jwt_required()(lambda: None)()
            return True
        except Exception as e:
            current_app.logger.error(f"JWT error: {str(e)}")
            return False

    def login_jwt(self, username, password):
        if username == current_app.config['BASIC_AUTH_USERNAME'] and password == current_app.config['BASIC_AUTH_PASSWORD']:
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401