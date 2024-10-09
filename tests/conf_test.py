import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.cosmos import CosmosClient
from app.encryption import Encryptor
from app.cosmos_db_client import CosmosDBClient
from unittest.mock import MagicMock
from app import create_app

@pytest.fixture(scope="session")
def app():
    load_dotenv()
    app = create_app()
    return app

@pytest.fixture(scope="session")
def client(app):
    return app.test_client()

@pytest.fixture(scope="session")
def azure_credential():
    return DefaultAzureCredential()

@pytest.fixture(scope="session")
def key_vault_client(azure_credential):
    key_vault_url = os.getenv('KEY_VAULT_URL')
    return SecretClient(vault_url=key_vault_url, credential=azure_credential)

@pytest.fixture(scope="session")
def cosmos_client(key_vault_client):
    cosmos_endpoint = os.getenv('COSMOS_ENDPOINT')
    cosmos_key = key_vault_client.get_secret('COSMOS-KEY').value
    return CosmosClient(cosmos_endpoint, cosmos_key)

@pytest.fixture(scope="session")
def cosmos_container(cosmos_client):
    database_name = os.getenv('DATABASE_NAME')
    container_name = os.getenv('CONTAINER_NAME')
    database = cosmos_client.get_database_client(database_name)
    return database.get_container_client(container_name)

@pytest.fixture
def encryptor():
    # Create a mock Encryptor
    mock_encryptor = MagicMock(spec=Encryptor)
    
    # Define behavior for encrypt and decrypt methods
    mock_encryptor.encrypt.side_effect = lambda x: f"encrypted_{x}"
    mock_encryptor.decrypt.side_effect = lambda x: x.replace("encrypted_", "")
    
    # Mock the rotate_key method
    mock_encryptor.rotate_key.return_value = "new_key_version"
    
    return mock_encryptor

@pytest.fixture(scope="session")
def cosmos_db_client(app):
    with app.app_context():
        return CosmosDBClient(app)