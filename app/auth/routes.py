from flask import request
from . import auth_bp

def init_auth_routes(auth):
    print("Initializing auth routes")
    @auth_bp.route('/login', methods=['POST'])
    def login():
        print("Login route called")
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        return auth.jwt_auth.login_jwt(username, password)

    @auth_bp.route('/login/github')
    def github_login():
        print("GitHub login route called")
        return auth.oauth_auth.oauth_login()

    @auth_bp.route('/login/github/callback')
    def github_callback():
        print("GitHub callback route called")
        return auth.oauth_auth.oauth_callback()

    return auth_bp