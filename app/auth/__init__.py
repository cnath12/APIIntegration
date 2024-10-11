from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from . import routes
from .base import Auth
from .jwt_auth import JWTAuth
from .oauth_auth import OAuthAuth
from .api_key_auth import APIKeyAuth

def init_auth(app):
    jwt_auth = JWTAuth(app)
    oauth_auth = OAuthAuth(app)
    api_key_auth = APIKeyAuth(app)
    auth = Auth(app, jwt_auth, oauth_auth, api_key_auth)
    routes.init_auth_routes(auth)
    print("Auth initialized")
    return auth