import requests
import json
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Your API base URL
BASE_URL = "http://localhost:5000"  # Adjust if your API is hosted elsewhere

# Key Vault and Cosmos DB configuration
KEY_VAULT_URL = "https://your-key-vault.vault.azure.net/"
COSMOS_ENDPOINT = "https://your-cosmos-db.documents.azure.com:443/"
DATABASE_NAME = "your_database_name"
CONTAINER_NAME = "your_container_name"

# Fetch Cosmos DB key from Key Vault
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
cosmos_key = secret_client.get_secret("COSMOS-KEY").value

# Initialize Cosmos DB client
cosmos_client = CosmosClient(COSMOS_ENDPOINT, credential=cosmos_key)
database = cosmos_client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

def test_encryption():
    # 1. Create a new item through your API
    new_item = {"name": "Test Encryption", "description": "This is a test"}
    response = requests.post(f"{BASE_URL}/users", json=new_item)
    assert response.status_code == 201, "Failed to create item"
    created_item = response.json()
    item_id = created_item['id']

    # 2. Retrieve the item through your API
    response = requests.get(f"{BASE_URL}/users/{item_id}")
    assert response.status_code == 200, "Failed to retrieve item"
    retrieved_item = response.json()
    assert retrieved_item['name'] == "Test Encryption", "Name should be decrypted in API response"

    # 3. Directly retrieve the item from Cosmos DB
    item_from_cosmos = container.read_item(item=item_id, partition_key=item_id)
    assert item_from_cosmos['name'] != "Test Encryption", "Name should be encrypted in Cosmos DB"

    print("Encryption test passed successfully!")

if __name__ == "__main__":
    test_encryption()