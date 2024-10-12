from flask import Blueprint, request, jsonify
import uuid
from functools import wraps
import tenacity
from . import api_bp
from azure.cosmos.exceptions import CosmosHttpResponseError
from azure.core.exceptions import AzureError
from ..rbac.utils import rbac_required
from ..models.role import Role
from ..models.user import User

def init_routes(bp, cosmos_client, auth, limiter):
    print("API routes file is being imported")
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
    @rbac_required(['read_user'])
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
    @rbac_required(['create_user'])
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
    
    @bp.route('/rotate-key', methods=['POST'])
    @auth.require_auth('any')
    @rate_limit_decorator()
    def rotate_encryption_key():
        try:
            new_version = cosmos_client.rotate_encryption_key()
            return jsonify({"message": f"Key rotated successfully. New version: {new_version}"}), 200
        except Exception as e:
            return jsonify({"error": f"Key rotation failed: {str(e)}"}), 500

    @bp.route('/test_encryption', methods=['POST', 'GET'])
    def test_encryption():
        if request.method == 'POST':
            data = request.json
            original_text = data.get('password', '')
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
    
    @bp.route('/roles', methods=['GET'])
    @auth.require_auth('any')
    @rbac_required(['manage_roles'])
    def get_roles():
        roles = cosmos_client.get_all_roles()
        return jsonify([role.to_dict() for role in roles]), 200

    @bp.route('/roles', methods=['POST'])
    @auth.require_auth('any')
    @rbac_required(['manage_roles'])
    def create_role():
        data = request.json
        new_role = Role(data['name'], data['permissions'])
        created_role = cosmos_client.create_role(new_role)
        return jsonify(created_role.to_dict()), 201
    
    

    return api_bp