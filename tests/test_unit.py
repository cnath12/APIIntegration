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

class TestAuth(unittest.TestCase):
    @classmethod
    @patch('app.cosmos_db_client.CosmosClient')
    @patch('flask_limiter.Limiter')
    @patch('authlib.integrations.flask_client.OAuth')
    def setUpClass(cls, mock_oauth, mock_limiter, mock_cosmos_client):
        test_config = {
            'TESTING': True,
            'API_KEY': 'test_api_key',
            'BASIC_AUTH_USERNAME': 'admin',
            'BASIC_AUTH_PASSWORD': 'admin',
            'COSMOS_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_KEY': 'test_key',
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container',
            'JWT_SECRET_KEY': 'test_jwt_secret',
            'GITHUB_CLIENT_ID': 'test_github_client_id',
            'GITHUB_CLIENT_SECRET': 'test_github_client_secret',
            'RATE_LIMIT' : 1000,
            'RATE_LIMIT_PERIOD': 3600,
        }
        cls.app = create_app(test_config)
        cls.client = cls.app.test_client()
        cls.auth = Auth(cls.app)

        # Mock OAuth
        cls.mock_oauth_instance = mock_oauth.return_value
        cls.mock_github = MagicMock()
        cls.mock_oauth_instance.register.return_value = cls.mock_github

    def setUp(self):
        print(f"\nSetting up test: {self._testMethodName}")

    def tearDown(self):
        print(f"Tearing down test: {self._testMethodName}")

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
    @patch('app.cosmos_db_client.CosmosClient')
    @patch('app.cosmos_db_client.DefaultAzureCredential')
    @patch('app.cosmos_db_client.SecretClient')
    @patch('app.cosmos_db_client.Encryptor')
    def setUp(self, mock_encryptor, mock_secret_client, mock_default_credential, mock_cosmos_client):
        self.app = MagicMock()
        self.app.config = {
            'COSMOS_ENDPOINT': 'https://test.documents.azure.com:443/',
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container',
            'KEY_VAULT_URL': 'https://test-keyvault.vault.azure.net/',
            'KEY_NAME': 'test-key-name'
        }
        
        # Mock the secret client to return a fake Cosmos DB key
        mock_secret_client_instance = mock_secret_client.return_value
        mock_secret_client_instance.get_secret.return_value.value = 'fake-cosmos-key'
        
        self.cosmos_client = CosmosDBClient(self.app)
        self.mock_cosmos_client = mock_cosmos_client
        self.mock_encryptor = mock_encryptor.return_value

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
        mock_container = self.cosmos_client.container
        mock_items = [
            {'id': '1', 'name': base64.b64encode(b'EncryptedTest1').decode()},
            {'id': '2', 'name': base64.b64encode(b'EncryptedTest2').decode()}
        ]
        mock_container.query_items.return_value = mock_items
        
        # Mock the decryption process
        self.mock_encryptor.decrypt.side_effect = ['Test1', 'Test2']
        
        items = self.cosmos_client.get_all_items()
        
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['name'], 'Test1')
        self.assertEqual(items[1]['name'], 'Test2')

    def test_create_item(self):
        mock_container = self.cosmos_client.container
        test_item = {'id': '1', 'name': 'Test Item'}
        
        # Mock the encryption process
        self.mock_encryptor.encrypt.return_value = 'EncryptedTestItem'
        
        self.cosmos_client.create_item(test_item)
        
        mock_container.create_item.assert_called_once()
        created_item = mock_container.create_item.call_args[1]['body']
        self.assertEqual(created_item['name'], 'EncryptedTestItem')

    def test_get_item(self):
        mock_container = self.cosmos_client.container
        mock_item = {'id': '1', 'name': 'EncryptedTest'}
        mock_container.read_item.return_value = mock_item
        
        # Mock the decryption process
        self.mock_encryptor.decrypt.return_value = 'Test'
        
        item = self.cosmos_client.get_item('1')
        
        self.assertEqual(item['name'], 'Test')

    def test_update_item(self):
        mock_container = self.cosmos_client.container
        test_item = {'id': '1', 'name': 'Updated Test Item'}
        
        # Mock the encryption process
        self.mock_encryptor.encrypt.return_value = 'EncryptedUpdatedTestItem'
        
        self.cosmos_client.update_item(test_item)
        
        mock_container.upsert_item.assert_called_once()
        updated_item = mock_container.upsert_item.call_args[1]['body']
        self.assertEqual(updated_item['name'], 'EncryptedUpdatedTestItem')

    def test_delete_item(self):
        mock_container = self.cosmos_client.container
        self.cosmos_client.delete_item('1')
        mock_container.delete_item.assert_called_once_with(item='1', partition_key='1')

if __name__ == '__main__':
    unittest.main()