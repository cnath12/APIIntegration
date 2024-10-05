from flask import Flask, jsonify, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from .cosmos_db_client import CosmosDBClient
from .auth import Auth
from . import routes
import os
from authlib.integrations.flask_client import OAuth
from .config import get_config
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_talisman import Talisman
import logging
from logging.handlers import RotatingFileHandler
from .utils import https_url_for, ensure_https


def create_app(test_config=None):
    load_dotenv()
    print("Environment variables loaded")
    app = Flask(__name__)

    if not app.debug and not os.environ.get('FLASK_ENV') == 'development':
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

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/application.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

    # Initialize Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=[f"{app.config['RATE_LIMIT']} per day", f"{app.config['RATE_LIMIT_PERIOD']} per hour"],
        storage_uri="memory://"
    )


    print(f"COSMOS_ENDPOINT: {app.config.get('COSMOS_ENDPOINT')}")
    print(f"KEY_VAULT_URL: {app.config.get('KEY_VAULT_URL')}")
    print("Initializing CosmosDBClient")
    cosmos_client = CosmosDBClient(app)
    print("CosmosDBClient initialized")
    oauth = OAuth(app)
    auth = Auth(app, oauth)

    # Configure OAuth for GitHub
    oauth.register(
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

    # Register routes
    app.register_blueprint(routes.init_routes(cosmos_client, auth, limiter))

    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f"404 error occurred: {request.url}")
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(401)
    def unauthorized(error):
        app.logger.warning(f"Unauthorized access attempt: {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f"Rate limit exceeded: {request.remote_addr}")
        return jsonify({"error": "Rate limit exceeded"}), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500
    
    @app.route('/favicon.ico')
    def favicon():
        return '', 204
    
    @app.before_request
    def force_https_redirects():
        if request.url.startswith('http://') and not app.debug:
            return redirect(ensure_https(request.url), code=301)


    return app