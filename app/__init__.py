from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from .config import Config
from .cosmos_db_client import CosmosDBClient
from .auth import Auth
from . import routes
import os

def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.update(test_config)

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    cosmos_client = CosmosDBClient(app)
    auth = Auth(app)

    app.register_blueprint(routes.init_routes(cosmos_client, auth, limiter))

    return app
