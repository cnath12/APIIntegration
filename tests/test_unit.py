import unittest
from unittest.mock import patch, MagicMock
import base64
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.auth import Auth
from app.cosmos_db_client import CosmosDBClient
from flask_jwt_extended import create_access_token

class MockConfig:
    TESTING = True
    COSMOS_ENDPOINT = 'https://test.documents.azure.com:443/'
    DATABASE_NAME = 'test_db'
    CONTAINER_NAME = 'test_container'
    KEY_VAULT_URL = 'https://test-keyvault.vault.azure.net/'
    KEY_NAME = 'test-key-name'
    API_KEY = 'test_api_key'
    BASIC_AUTH_USERNAME = 'admin'
    BASIC_AUTH_PASSWORD = 'admin'
    GITHUB_CLIENT_ID = 'test_github_client_id'
    GITHUB_CLIENT_SECRET = 'test_github_client_secret'
    JWT_SECRET_KEY = 'test_jwt_secret'
    SECRET_KEY = 'test_secret_key'
    RATE_LIMIT = 1000
    RATE_LIMIT_PERIOD = 3600

    @classmethod
    def load_secrets(cls):
        cls.COSMOS_KEY = 'test_cosmos_key'

class TestCosmosDBClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        
        # Mock the DefaultAzureCredential
        cls.credential_patcher = patch('azure.identity.DefaultAzureCredential')
        cls.mock_credential = cls.credential_patcher.start()
        
        # Mock the SecretClient
        cls.secret_client_patcher = patch('azure.keyvault.secrets.SecretClient')
        cls.mock_secret_client = cls.secret_client_patcher.start()
        cls.mock_secret_client.return_value.get_secret.return_value.value = 'fake-cosmos-key'
        
        # Mock the CosmosClient
        cls.cosmos_client_patcher = patch('azure.cosmos.CosmosClient')
        cls.mock_cosmos_client = cls.cosmos_client_patcher.start()
        
        # Mock the Encryptor
        cls.encryptor_patcher = patch('app.encryption.Encryptor')
        cls.mock_encryptor = cls.encryptor_patcher.start()

        with cls.app.app_context():
            cls.cosmos_client = cls.app.extensions['cosmos_client']

    @classmethod
    def tearDownClass(cls):
        cls.credential_patcher.stop()
        cls.secret_client_patcher.stop()
        cls.cosmos_client_patcher.stop()
        cls.encryptor_patcher.stop()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_check_api_key(self):
        with self.app.test_request_context(headers={'X-API-Key': 'test_api_key'}):
            result = self.auth.check_api_key()
            self.assertTrue(result)

    def test_check_basic_auth(self):
        auth_string = base64.b64encode(b'admin:admin').decode('utf-8')
        with self.app.test_request_context(headers={'Authorization': f'Basic {auth_string}'}):
            result = self.auth.check_basic_auth()
            self.assertTrue(result)

    def test_jwt_login(self):
        response = self.client.post('/login', json={
            'username': 'admin',
            'password': 'admin'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json)

    def test_jwt_protected_route(self):
        # First, get a token
        response = self.client.post('/login', json={
            'username': 'admin',
            'password': 'admin'
        })
        token = response.json['access_token']

        # Then, use the token to access a protected route
        response = self.client.get('/users', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)

    @patch('app.auth.Auth.github')
    def test_github_login(self, mock_github):
        mock_github.authorize_redirect.return_value = 'Redirecting...'
        response = self.client.get('/login/github')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'Redirecting...')

    @patch('app.auth.Auth.github')
    def test_github_callback(self, mock_github):
        mock_github.authorize_access_token.return_value = 'mock_token'
        mock_github.get.return_value.json.return_value = {'login': 'test_user'}
        response = self.client.get('/login/github/callback')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.json)

class TestCosmosDBClient(unittest.TestCase):
    @patch('app.get_config')
    @patch('app.cosmos_db_client.CosmosClient')
    @patch('app.cosmos_db_client.DefaultAzureCredential')
    @patch('app.cosmos_db_client.SecretClient')
    @patch('app.cosmos_db_client.Encryptor')
    def setUp(self, mock_encryptor, mock_secret_client, mock_default_credential, mock_cosmos_client, mock_get_config):
        mock_get_config.return_value = MockConfig
        self.app = create_app()
        
        # Mock the secret client to return a fake Cosmos DB key
        mock_secret_client_instance = mock_secret_client.return_value
        mock_secret_client_instance.get_secret.return_value.value = 'fake-cosmos-key'
        
        self.mock_cosmos_client = mock_cosmos_client
        self.mock_encryptor = mock_encryptor.return_value

        # Create the CosmosDBClient instance
        self.cosmos_client = CosmosDBClient(self.app)

        # Reset the mock to clear the call count
        self.mock_cosmos_client.reset_mock()

    def test_initialization(self):
        self.mock_cosmos_client.assert_called_once_with(
            'https://test.documents.azure.com:443/',
            credential='fake-cosmos-key'
        )
        self.assertIsNotNone(self.cosmos_client.client)
        self.assertIsNotNone(self.cosmos_client.database)
        self.assertIsNotNone(self.cosmos_client.container)
        self.assertIsNotNone(self.cosmos_client.encryptor)

    def test_get_all_items(self):
        #mock_container = self.cosmos_client.container
        mock_items = [
            {'id': '1', 'name': base64.b64encode(b'EncryptedTest1').decode()},
            {'id': '2', 'name': base64.b64encode(b'EncryptedTest2').decode()}
        ]
        self.cosmos_client.container.query_items.return_value = mock_items
        
        # Mock the decryption process
        self.mock_encryptor.decrypt.side_effect = ['Test1', 'Test2']
        
        items = self.cosmos_client.get_all_items()
        
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['name'], 'Test1')
        self.assertEqual(items[1]['name'], 'Test2')

    def test_create_item(self):
        test_item = {'id': '1', 'name': 'Test Item'}
        self.mock_encryptor.encrypt.return_value = 'EncryptedTestItem'
        
        self.cosmos_client.create_item(test_item)
        
        self.cosmos_client.container.create_item.assert_called_once()
        called_args = self.cosmos_client.container.create_item.call_args
        self.assertEqual(called_args[0][0]['name'], 'EncryptedTestItem')

    def test_get_item(self):
        mock_item = {'id': '1', 'name': 'EncryptedTest'}
        self.cosmos_client.container.read_item.return_value = mock_item
        self.mock_encryptor.decrypt.return_value = 'Test'
        
        item = self.cosmos_client.get_item('1')
        
        self.assertEqual(item['name'], 'Test')
        self.cosmos_client.container.read_item.assert_called_once_with(item='1', partition_key='1')

    def test_update_item(self):
        test_item = {'id': '1', 'name': 'Updated Test Item'}
        self.mock_encryptor.encrypt.return_value = 'EncryptedUpdatedTestItem'
        
        self.cosmos_client.update_item(test_item)
        
        self.cosmos_client.container.upsert_item.assert_called_once()
        called_args = self.cosmos_client.container.upsert_item.call_args
        self.assertEqual(called_args[0][0]['name'], 'EncryptedUpdatedTestItem')

    def test_delete_item(self):
        self.cosmos_client.delete_item('1')
        self.cosmos_client.container.delete_item.assert_called_once_with(item='1', partition_key='1')

    @patch('app.cosmos_db_client.Encryptor')
    def test_encryption(self, mock_encryptor):
        mock_encryptor_instance = MagicMock()
        mock_encryptor_instance.encrypt.return_value = 'encrypted_text'
        mock_encryptor_instance.decrypt.return_value = 'decrypted_text'
        mock_encryptor.return_value = mock_encryptor_instance

        self.cosmos_client.encryptor = mock_encryptor_instance

        original_text = "This is a test"
        encrypted_text = self.cosmos_client.encryptor.encrypt(original_text)
        decrypted_text = self.cosmos_client.encryptor.decrypt(encrypted_text)

        self.assertEqual(encrypted_text, 'encrypted_text')
        self.assertEqual(decrypted_text, 'decrypted_text')

if __name__ == '__main__':
    unittest.main()