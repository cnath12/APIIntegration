from flask import Blueprint, request, jsonify, url_for
import uuid
import time
from functools import wraps
import tenacity

bp = Blueprint('users', __name__)

def init_routes(cosmos_client, auth, limiter):
    def rate_limit_decorator():
        return limiter.limit("100/minute")

    def exponential_backoff(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return tenacity.retry(
                wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
                stop=tenacity.stop_after_attempt(5),
                retry=tenacity.retry_if_exception_type(Exception)
            )(func)(*args, **kwargs)
        return wrapper
        
    @bp.route('/users', methods=['GET'])
    @auth.require_auth('any')
    @limiter.limit("100/minute")
    def get_users():
            try:
                users = cosmos_client.get_all_items()
                return jsonify(users), 200
            except Exception as e:
                current_app.logger.error(f"Error in get_users: {str(e)}")
                return jsonify({"error": "Internal server error"}), 500

    # @bp.route('/users', methods=['GET'])
    # @auth.require_auth('any')
    # @limiter.limit("100/minute")
    # def get_users():
    #     try:
    #         limit = request.args.get('limit', default=100, type=int)
    #         offset = request.args.get('offset', type=int)
    #         continuation_token = request.args.get('continuation_token')
    #         users = cosmos_client.get_all_items() 
            
    #         response = {
    #             'users': users[:limit],
    #             'limit': limit,
    #         }
    #         if len(users)>limit:
    #             if(continuation_token):
    #                 response['next_page'] = url_for(
    #                     'users.get_users',
    #                     limit=limit,
    #                     continuation_token=next_continuation_token,
    #                     _external=True
    #                 )
    #         elif offset is not None:
    #             next_offset = offset + limit
    #             response['next_page'] = url_for(
    #                 'users.get_users',
    #                 limit=limit,
    #                 offset=next_offset,
    #                 _external=True
    #             )
    #         return jsonify(response), 200
    #     except Exception as e:
    #         current_app.logger.error(f"Error in get_users: {str(e)}")
    #         return jsonify({"error": "Internal server error"}), 500


    @bp.route('/users', methods=['POST'])
    @auth.require_auth('any')
    @rate_limit_decorator()
    @exponential_backoff
    def create_user():
        new_user = request.json
        if 'id' not in new_user:
            new_user['id'] = str(uuid.uuid4())
        created_user = cosmos_client.create_item(new_user)
        return jsonify(created_user), 201

    @bp.route('/users/<string:id>', methods=['GET'])
    @auth.require_auth('any')
    @rate_limit_decorator()
    @exponential_backoff
    def get_user(id):
        user = cosmos_client.get_item(id)
        if user:
            return jsonify(user), 200
        return jsonify({"error": "User not found"}), 404

    @bp.route('/users/<string:id>', methods=['PUT'])
    @auth.require_auth('any')
    @rate_limit_decorator()
    @exponential_backoff
    def update_user(id):
        update_data = request.json
        update_data['id'] = id
        updated_user = cosmos_client.update_item(update_data)
        return jsonify(updated_user), 200

    @bp.route('/users/<string:id>', methods=['DELETE'])
    @auth.require_auth('any')
    @rate_limit_decorator()
    @exponential_backoff
    def delete_user(id):
        cosmos_client.delete_item(id)
        return '', 204

    @bp.route('/login/github')
    @rate_limit_decorator()
    def github_login():
        return auth.oauth_login()

    @bp.route('/login/github/callback')
    @rate_limit_decorator()
    def github_callback():
        return auth.oauth_callback()

    return bp