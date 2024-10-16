from azure.cosmos import CosmosClient, exceptions
import uuid
import tenacity
from ..security.encryption import Encryptor
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import base64
from ..models.role import Role
from ..models.user import User


class CosmosDBClient:
    def __init__(self, app):
        cosmos_endpoint = app.config.get('COSMOS_ENDPOINT')
        database_name = app.config.get('DATABASE_NAME')
        container_name = app.config.get('CONTAINER_NAME')
        key_vault_url = app.config.get('KEY_VAULT_URL')
        key_name = app.config.get('KEY_NAME')
        
        if not all([cosmos_endpoint, database_name, container_name, key_vault_url, key_name]):
            raise ValueError("Missing Cosmos DB or Key Vault configuration")
        
        try:
            credential = DefaultAzureCredential(additionally_allowed_tenants=["*"])
            secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
            cosmos_key = secret_client.get_secret('COSMOS-KEY').value
            
            self.client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
            self.database = self.client.get_database_client(database_name)
            self.container = self.database.get_container_client(container_name)
            print("About to initialize Encryptor")
            self.encryptor = Encryptor(key_vault_url, key_name)
            print("Encryptor initialized")
        except Exception as e:
            print(f"Error initializing CosmosDBClient: {str(e)}")
            raise

    
    def _decrypt_item(self, item):
        if 'name' in item:
            encrypted_name = item['name']
            print(f"Attempting to decrypt: {encrypted_name}")
            try:
                # Ensure the encrypted name is properly padded
                padding = 4 - (len(encrypted_name) % 4)
                if padding:
                    encrypted_name += '=' * padding
                
                decoded_name = base64.b64decode(encrypted_name)
                decrypted_name = self.encryptor.decrypt(decoded_name)
                item['name'] = decrypted_name
                print(f"Successfully decrypted: {decrypted_name}")
            except Exception as decrypt_error:
                print(f"Error decrypting name for item {item.get('id', 'unknown')}: {str(decrypt_error)}")
        return item

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def get_all_items(self):
        try:
            query = "SELECT * FROM c"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            return [self._decrypt_item(item) for item in items]
        except exceptions.CosmosHttpResponseError as e:
            print(f"Cosmos DB HTTP Error in get_all_items: {str(e)}")
            print(f"Status code: {e.status_code}")
            print(f"Substatus: {e.sub_status}")
            print(f"Error code: {e.error_code}")
            raise
        except Exception as e:
            print(f"Unexpected error in get_all_items: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            raise

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def create_item(self, item):
        if 'id' not in item:
            item['id'] = str(uuid.uuid4())
        if 'name' in item:
            item['name'] = self.encryptor.encrypt(item['name'])
        return self.container.create_item(body=item)

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def get_item(self, id):
        try:
            item = self.container.read_item(item=id, partition_key=id)
            if 'name' in item:
                item['name'] = self.encryptor.decrypt(item['name'])
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def update_item(self, item):
        if 'name' in item:
            item['name'] = self.encryptor.encrypt(item['name'])
        return self.container.upsert_item(body=item)

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def delete_item(self, id):
        self.container.delete_item(item=id, partition_key=id)


    def re_encrypt_all_items(self):
        query = "SELECT * FROM c"
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        for item in items:
            if 'name' in item:
                decrypted_name = self.encryptor.decrypt(item['name'])
                item['name'] = self.encryptor.encrypt(decrypted_name)
                self.container.upsert_item(body=item)

    def rotate_encryption_key(self):
        new_version = self.encryptor.rotate_key()
        self.re_encrypt_all_items()
        return new_version
    

    def get_all_roles(self):
        query = "SELECT * FROM c WHERE c.type = 'role'"
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        return [Role.from_dict(item) for item in items]

    def create_role(self, role):
        role_dict = role.to_dict()
        role_dict['type'] = 'role'  # Add a type field to distinguish roles from other documents
        created_item = self.container.create_item(body=role_dict)
        return Role.from_dict(created_item)

    def get_role_by_name(self, name):
        query = f"SELECT * FROM c WHERE c.type = 'role' AND c.name = @name"
        parameters = [{"name": "@name", "value": name}]
        items = list(self.container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        return Role.from_dict(items[0]) if items else None

    def update_role(self, role):
        role_dict = role.to_dict()
        role_dict['type'] = 'role'
        updated_item = self.container.upsert_item(body=role_dict)
        return Role.from_dict(updated_item)

    def delete_role(self, role_id):
        self.container.delete_item(item=role_id, partition_key=role_id)

    # Update user-related methods to handle roles
    def create_user(self, user):
        user_dict = user.to_dict()
        user_dict['type'] = 'user'  # Add a type field to distinguish users from other documents
        created_item = self.container.create_item(body=user_dict)
        return User.from_dict(created_item)

    def get_user_by_username(self, username):
        query = f"SELECT * FROM c WHERE c.type = 'user' AND c.username = @username"
        parameters = [{"name": "@username", "value": username}]
        items = list(self.container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        return User.from_dict(items[0]) if items else None
