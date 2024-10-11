import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from flask import Flask, jsonify, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_talisman import Talisman
from authlib.integrations.flask_client import OAuth

from config import get_config
from .data.cosmos_db_client import CosmosDBClient
from .auth import auth_bp, init_auth
from .api import init_api
from .api.routes import init_routes
from .auth.oauth import configure_oauth
from .logging.setup import configure_logging
from .error_handlers import register_error_handlers
from .utils.helpers import ensure_https

limiter = Limiter(key_func=get_remote_address)
cosmos_client = None

def create_app(test_config=None):
    load_dotenv()
    print("Environment variables loaded")
    app = Flask(__name__)

    if not app.debug and os.environ.get('FLASK_ENV') != 'development':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    
    if test_config is None:
        print("Loading configuration")
        config_class = get_config()
        print(f"Config class: {config_class.__name__}")
        app.config.from_object(config_class)
        print("Configuration loaded, attempting to load secrets")
        try:
            config_class.load_secrets()
            print("Secrets loaded successfully")
            for key in dir(config_class):
                if key.isupper():
                    app.config[key] = getattr(config_class, key)
        except Exception as e:
            print(f"Error loading secrets: {str(e)}")
    else:
        app.config.update(test_config)

    configure_logging(app)

    cosmos_client = CosmosDBClient(app)
    if not hasattr(app, 'auth_initialized'):
        auth = init_auth(app)
        app.auth_initialized = True
    print("After auth initialization")

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[f"{app.config['RATE_LIMIT']} per day", f"{app.config['RATE_LIMIT_PERIOD']} per hour"],
        storage_uri="memory://"
    )

    oauth = OAuth(app)
    configure_oauth(app, oauth)

    # Content Security Policy
    csp = {
        'default-src': '\'self\'',
        'style-src': '\'self\' https://fonts.googleapis.com',
        'font-src': '\'self\' https://fonts.gstatic.com',
        'script-src': '\'self\' https://cdnjs.cloudflare.com',
        'img-src': '\'self\' data:',
    }

    # Initialize Talisman with CSP
    
    Talisman(app, force_https=not app.debug, frame_options='DENY', x_xss_protection=False, 
             strict_transport_security=True, session_cookie_secure=not app.debug, 
             content_security_policy=csp, referrer_policy='strict-origin-when-cross-origin'
            )

    app.register_blueprint(auth_bp, url_prefix='/auth')
    api_blueprint = init_api(cosmos_client, auth, limiter)  # Initialize API routes
    app.register_blueprint(api_blueprint, url_prefix='/api')

    register_error_handlers(app)
    
    
    
    @app.route('/favicon.ico')
    def favicon():
        return '', 204
    
    @app.before_request
    def force_https_redirects():
        if request.url.startswith('http://') and not app.debug:
            return redirect(ensure_https(request.url), code=301)


    return app