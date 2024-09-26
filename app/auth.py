from flask import request, jsonify, current_app, url_for
from functools import wraps
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from authlib.integrations.flask_client import OAuth
import os

class Auth:
    def __init__(self, app, oauth):
        self.app = app
        self.jwt = JWTManager(app)
        self.oauth = OAuth(app)

        # Configure JWT
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')  # Change this!

        # Configure OAuth
        app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID')
        app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET')

        self.github = self.oauth.register(
            name='github',
            client_id=app.config['GITHUB_CLIENT_ID'],
            client_secret=app.config['GITHUB_CLIENT_SECRET'],
            access_token_url='https://github.com/login/oauth/access_token',
            access_token_params=None,
            authorize_url='https://github.com/login/oauth/authorize',
            authorize_params=None,
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'},
        )

    def require_auth(self, auth_type='any'):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                auth_successful = False
                if auth_type == 'any':
                    auth_successful = self.check_api_key() or self.check_basic_auth() or self.check_jwt()
                elif auth_type == 'api_key':
                    auth_successful = self.check_api_key()
                elif auth_type == 'basic':
                    auth_successful = self.check_basic_auth()
                elif auth_type == 'jwt':
                    return jwt_required()(f)(*args, **kwargs)
                
                if auth_successful:
                    return f(*args, **kwargs)
                else:
                    return jsonify({"error": "Unauthorized"}), 401
            return decorated_function
        return decorator

    def check_api_key(self):
        api_key = request.headers.get('X-API-Key')
        if api_key is None:
            return False
        result = api_key == self.app.config['API_KEY']
        return result

    def check_basic_auth(self):
        auth = request.authorization
        if not auth:
            print("No authorization header found")
            return False
        result = auth.username == self.app.config['BASIC_AUTH_USERNAME'] and \
                 auth.password == self.app.config['BASIC_AUTH_PASSWORD']
        return result

    def check_jwt(self):
        try:
            jwt_required()(lambda: None)()
            return True
        except:
            return False

    def login_jwt(self, username, password):
        if username == self.app.config['BASIC_AUTH_USERNAME'] and password == self.app.config['BASIC_AUTH_PASSWORD']:
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    def oauth_login(self):
        redirect_uri = url_for('users.github_callback', _external=True)
        return self.github.authorize_redirect(redirect_uri)

    def oauth_callback(self):
        try:
            token = self.github.authorize_access_token()
            resp = self.github.get('user', token=token)
            github_user = resp.json()
            
            # Use the GitHub username as the identity for the JWT
            # This doesn't require storing any user data
            access_token = create_access_token(identity=github_user['login'])
            
            return jsonify(
                message="Successfully authenticated with GitHub",
                github_username=github_user['login'],
                access_token=access_token
            ), 200
        except Exception as e:
            # Log the error for debugging
            current_app.logger.error(f"OAuth callback error: {str(e)}")
            return jsonify(error="Authentication failed"), 400


        # token = self.github.authorize_access_token()
        # resp = self.github.get('user', token=token)
        # profile = resp.json()
        # #implement creation or update of user. 
        # access_token = create_access_token(identity=profile['login'])
        # return jsonify(access_token=access_token), 200
        