from azure.cosmos import CosmosClient, exceptions
import uuid
import tenacity
from .encryption import Encryptor
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import base64


class CosmosDBClient:
    def __init__(self, app):
        print("CosmosDBClient initialization started")
        print(f"KEY_VAULT_URL: {app.config.get('KEY_VAULT_URL')}")
        print(f"KEY_NAME: {app.config.get('KEY_NAME')}")
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

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def get_all_items(self):
        try:
            query = "SELECT * FROM c"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            decrypted_items = []
            for item in items:
                try:
                    if 'name' in item:
                        encrypted_name = item['name']
                        print(f"Encrypted name: {encrypted_name}")
                        try:
                            # Try to add padding if it's missing
                            padding_needed = len(encrypted_name) % 4
                            if padding_needed:
                                encrypted_name += '=' * (4 - padding_needed)
                            
                            decoded_name = base64.b64decode(encrypted_name)
                            item['name'] = self.encryptor.decrypt(decoded_name)
                        except Exception as decrypt_error:
                            print(f"Error decrypting name for item {item.get('id', 'unknown')}: {str(decrypt_error)}")
                            item['name'] = f"[Decryption Error: {str(decrypt_error)}]"
                except Exception as item_error:
                    print(f"Error processing item: {str(item_error)}")
                decrypted_items.append(item)
            return decrypted_items
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