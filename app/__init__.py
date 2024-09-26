from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from .config import Config
from .cosmos_db_client import CosmosDBClient
from .auth import Auth
from . import routes
import os
from authlib.integrations.flask_client import OAuth

def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.update(test_config)

    # Set the secret key
    app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24) #how do we handle this? 
                                                                    #just a placeholder
                                                                    #random for now

    # Initialize Limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    cosmos_client = CosmosDBClient(app)
    oauth = OAuth(app)
    auth = Auth(app,oauth)

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