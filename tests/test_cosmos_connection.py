import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, exceptions
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

load_dotenv()

def get_secret_from_key_vault(secret_name):
    key_vault_url = os.getenv('KEY_VAULT_URL')
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
    try:
        return secret_client.get_secret(secret_name).value
    except Exception as e:
        print(f"Error retrieving secret from Key Vault: {str(e)}")
        return None

def test_connection():
    try:
        cosmos_key = get_secret_from_key_vault('COSMOS-KEY')
        if not cosmos_key:
            raise ValueError("Failed to retrieve Cosmos DB key from Key Vault")

        client = CosmosClient(os.getenv('COSMOS_ENDPOINT'), credential=cosmos_key)
        database = client.get_database_client(os.getenv('DATABASE_NAME'))
        container = database.get_container_client(os.getenv('CONTAINER_NAME'))
        
        items = list(container.read_all_items(max_item_count=100))
        print(f"Successfully connected to Cosmos DB. Found {len(items)} items.")
        return True
    except exceptions.CosmosHttpResponseError as e:
        print(f"Failed to connect to Cosmos DB: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()