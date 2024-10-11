from flask import Blueprint

api_bp = Blueprint('api', __name__)

def init_api(cosmos_client, auth, limiter):
    from . import routes
    routes.init_routes(api_bp, cosmos_client, auth, limiter)

    return api_bp