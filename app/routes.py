from flask import Blueprint, request, jsonify
import uuid
import time
from functools import wraps
import tenacity
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.core.exceptions import AzureError


def init_routes(cosmos_client, auth, limiter):
    bp = Blueprint('users', __name__)
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
    
    @bp.route('/')
    @limiter.limit("100/minute")
    def home():
        return "Welcome to the API"

    @bp.route('/users', methods=['GET'])
    @auth.require_auth('any')
    @limiter.limit("100/minute")
    def get_users():
            try:
                users = cosmos_client.get_all_items()
                return jsonify(users), 200
            except CosmosHttpResponseError as e:
                print(f"Cosmos DB HTTP Error: {str(e)}")
                print(f"Status code: {e.status_code}")
                print(f"Substatus: {e.sub_status}")
                print(f"Error code: {e.error_code}")
                return jsonify({"error": "Database error", "details": str(e)}), 500
            except AzureError as e:
                print(f"Azure Error: {str(e)}")
                return jsonify({"error": "Azure service error", "details": str(e)}), 500
            except Exception as e:
                print(f"Unexpected error in get_users: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                return jsonify({"error": "Internal server error", "details": str(e)}), 500

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

    @bp.route('/login', methods=['POST'])
    @rate_limit_decorator()
    def login():
        username = request.json.get('username', None)
        password = request.json.get('password', None)
        return auth.login_jwt(username, password)

    @bp.route('/login/github')
    @rate_limit_decorator()
    def github_login():
        return auth.oauth_login()

    @bp.route('/login/github/callback')
    @rate_limit_decorator()
    def github_callback():
        return auth.oauth_callback()
    
    # @bp.route('/test_encryption', methods=['POST'])
    # def test_encryption():
    #     try:
    #         data = request.json
    #         if not data or 'password' not in data:
    #             return jsonify({'error': 'No password provided in request'}), 400

    #         original_text = data['password']
            
    #         # Encrypt the text
    #         encrypted_text = cosmos_client.encryptor.encrypt(original_text)
            
    #         # Decrypt the text
    #         decrypted_text = cosmos_client.encryptor.decrypt(encrypted_text)
            
    #         return jsonify({
    #             'original': original_text,
    #             'encrypted': encrypted_text,
    #             'decrypted': decrypted_text
    #         })
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 500

    @bp.route('/test_encryption', methods=['POST', 'GET'])
    def test_encryption():
        if request.method == 'POST':
            data = request.json
            original_text = data.get('text', '')
        else:  # GET request
            original_text = "secret"
        
        # Encrypt the text
        encrypted_text = cosmos_client.encryptor.encrypt(original_text)
        
        # Decrypt the text
        decrypted_text = cosmos_client.encryptor.decrypt(encrypted_text)
        
        return jsonify({
            'original': original_text,
            'encrypted': encrypted_text,
            'decrypted': decrypted_text
        })
    

    @bp.route('/test-https')
    def test_https():
        if request.is_secure:
            return jsonify({"status": "secure", "protocol": "HTTPS"}), 200
        else:
            return jsonify({"status": "not secure", "protocol": "HTTP"}), 200
    

    return bp