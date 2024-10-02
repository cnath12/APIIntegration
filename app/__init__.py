from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from .cosmos_db_client import CosmosDBClient
from .auth import Auth
from . import routes
import os
from authlib.integrations.flask_client import OAuth
from .config import get_config
from .cosmos_db_client import CosmosDBClient


def create_app(test_config=None):
    load_dotenv()
    print("Environment variables loaded")
    app = Flask(__name__)
    
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

    # Register routes
    app.register_blueprint(routes.init_routes(cosmos_client, auth, limiter))

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({"error": "Rate limit exceeded"}), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500

    return app