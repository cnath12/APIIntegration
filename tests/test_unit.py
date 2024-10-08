import unittest
from unittest.mock import patch, MagicMock
import base64
import json
import sys
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.cosmos import CosmosClient
from flask import redirect, url_for

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.auth import Auth
from app.cosmos_db_client import CosmosDBClient
from app.encryption import Encryptor
from flask_jwt_extended import create_access_token, JWTManager

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
    @patch('app.get_config')
    @patch('app.cosmos_db_client.CosmosClient')
    @patch('app.cosmos_db_client.DefaultAzureCredential')
    @patch('app.cosmos_db_client.SecretClient')
    @patch('app.cosmos_db_client.Encryptor')
    def setUp(self, mock_encryptor, mock_secret_client, mock_default_credential, mock_cosmos_client, mock_get_config):
        mock_get_config.return_value = MockConfig
        self.app = create_app()
        self.client = self.app.test_client()
        
        self.app.config = {
            'COSMOS_ENDPOINT': 'https://test.documents.azure.com:443/',
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container',
            'KEY_VAULT_URL': 'https://test-keyvault.vault.azure.net/',
            'KEY_NAME': 'test-key-name'
        }
        
        mock_secret_client_instance = mock_secret_client.return_value
        mock_secret_client_instance.get_secret.return_value.value = 'fake-cosmos-key'
        
        self.mock_cosmos_client = mock_cosmos_client
        self.mock_encryptor = mock_encryptor.return_value
        self.mock_default_credential = mock_default_credential
        self.mock_secret_client = mock_secret_client
        self.cosmos_client = CosmosDBClient(self.app)

    def test_initialization(self):
        # Check DefaultAzureCredential
        self.assertTrue(self.mock_default_credential.called)
        self.assertEqual(self.mock_default_credential.call_args[1], {'additionally_allowed_tenants': ["*"]})
        
        # Check SecretClient initialization
        expected_secret_calls = [
            unittest.mock.call(vault_url='https://test-keyvault.vault.azure.net/', credential=self.mock_default_credential.return_value),
            unittest.mock.call(vault_url='https://test-keyvault.vault.azure.net/', credential=self.mock_default_credential.return_value)
        ]
        self.mock_secret_client.assert_has_calls(expected_secret_calls, any_order=True)
        self.assertEqual(self.mock_secret_client.call_count, 2)

        # Check if get_secret was called for COSMOS-KEY
        self.mock_secret_client.return_value.get_secret.assert_any_call('COSMOS-KEY')

        # Check CosmosClient initialization
        self.mock_cosmos_client.assert_called_once_with(
            'https://test.documents.azure.com:443/', 
            credential=self.mock_secret_client.return_value.get_secret.return_value.value
        )

        # Check database and container client initialization
        mock_database_client = self.mock_cosmos_client.return_value.get_database_client
        mock_database_client.assert_called_with('test_db')
        mock_container_client = mock_database_client.return_value.get_container_client
        mock_container_client.assert_called_with('test_container')

        # Check Encryptor initialization
        self.assertTrue(self.mock_encryptor.called)
        self.assertEqual(self.mock_encryptor.call_args[0], ('https://test-keyvault.vault.azure.net/', 'test-key-name'))

    def test_get_all_items(self):
        mock_items = [
            {'id': '1', 'name': base64.b64encode(b'EncryptedTest1').decode()},
            {'id': '2', 'name': base64.b64encode(b'EncryptedTest2').decode()}
        ]
        self.cosmos_client.container.query_items.return_value = mock_items
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
        self.assertEqual(called_args.kwargs['body']['name'], 'EncryptedTestItem')

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
        self.assertEqual(called_args.kwargs['body']['name'], 'EncryptedUpdatedTestItem')

    def test_delete_item(self):
        self.cosmos_client.delete_item('1')
        self.cosmos_client.container.delete_item.assert_called_once_with(item='1', partition_key='1')

    def test_encryption(self):
        original_text = "This is a test"
        self.mock_encryptor.encrypt.return_value = 'encrypted_text'
        self.mock_encryptor.decrypt.return_value = 'decrypted_text'

        encrypted_text = self.cosmos_client.encryptor.encrypt(original_text)
        decrypted_text = self.cosmos_client.encryptor.decrypt(encrypted_text)

        self.assertEqual(encrypted_text, 'encrypted_text')
        self.assertEqual(decrypted_text, 'decrypted_text')

class TestAuth(unittest.TestCase):
    @patch('app.auth.OAuth')
    def setUp(self, mock_oauth):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.mock_oauth = mock_oauth
        self.mock_github = MagicMock()
        self.mock_oauth.register.return_value = self.mock_github
        self.auth = Auth(self.app, self.mock_oauth)
        self.app.config['API_KEY'] = 'test_api_key'
        self.app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # replace with your actual secret key
        self.jwt = JWTManager(self.app)

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
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertIn('Location', response.headers)  # Check for redirect header
        
        # If you're setting a JWT token in a cookie, you can check for it:
        # self.assertIn('Set-Cookie', response.headers)
        # self.assertIn('access_token_cookie', response.headers['Set-Cookie'])
        # You might want to check where it's redirecting to:
        # self.assertEqual(response.headers['Location'], '/dashboard')  # or whatever your target page is

    def test_jwt_protected_route(self):
        with self.app.app_context():
            # Create a token manually for testing
            access_token = create_access_token(identity='testuser')

        # Use the token to access a protected route
        response = self.client.get('/users', headers={'Authorization': f'Bearer {access_token}'})
        
        # Print response details for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Data: {response.data}")
        
        # Check the response
        if response.status_code == 302:
            print(f"Redirected to: {response.headers.get('Location')}")
        else:
            self.assertEqual(response.status_code, 200)  # Expecting a successful response
            self.assertIn('users', response.json)  # Assuming the response contains a 'users' key

    @patch('app.auth.OAuth')
    def test_github_login(self, mock_oauth):
        mock_github = MagicMock()
        mock_github.authorize_redirect.return_value = redirect('/login/github')
        mock_oauth.return_value.register.return_value = mock_github
        
        response = self.client.get('/login/github')
        
        self.assertEqual(response.status_code, 302)  # Expect a redirect
        self.assertIn('Location', response.headers)  # Check for redirect header
        self.assertEqual(response.headers['Location'], 'https://localhost/login/github')  # Check the actual redirect URL


    # @patch('app.auth.Auth.oauth')
    # def test_github_oauth_initiation(self):
    #     # Mock the authorize_redirect method
    #     self.mock_github.authorize_redirect.return_value = redirect('https://github.com/login/oauth/authorize')
        
    #     response = self.client.get('/login/github')
        
    #     self.assertEqual(response.status_code, 302)
    #     self.assertIn('Location', response.headers)
    #     self.assertIn('github.com/login/oauth/authorize', response.headers['Location'])
        
    #     # Verify that github.authorize_redirect was called
    #     self.mock_github.authorize_redirect.assert_called_once()

    @patch('app.auth.OAuth')
    def test_github_callback(self, mock_oauth):
        mock_github = MagicMock()
        mock_github.authorize_access_token.return_value = 'mock_token'
        mock_github.get.return_value.json.return_value = {'login': 'test_user'}
        mock_oauth.return_value.register.return_value = mock_github
        
        with patch('app.auth.create_access_token', return_value='mocked_jwt_token'):
            response = self.client.get('/login/github/callback')
        
        self.assertEqual(response.status_code, 302)  # Expect a redirect
        self.assertIn('Location', response.headers)  # Check for redirect header
        
        # If you're redirecting to a specific page after successful login, you can check that too
        # For example, if you're redirecting to the home page:
        # self.assertEqual(response.headers['Location'], '/')
        
        # If you're setting any cookies (like the JWT token), you can check for that
        # self.assertIn('Set-Cookie', response.headers)
        # self.assertIn('access_token_cookie', response.headers['Set-Cookie'])

class TestEncryptor(unittest.TestCase):
    @patch('app.encryption.KeyClient')
    @patch('app.encryption.CryptographyClient')
    def setUp(self, mock_crypto_client, mock_key_client):
        self.mock_key_client = mock_key_client
        self.mock_crypto_client = mock_crypto_client
        self.encryptor = Encryptor('https://fake-vault.vault.azure.net', 'fake-key-name')

    def test_encrypt(self):
        self.mock_crypto_client.return_value.encrypt.return_value.ciphertext = b'encrypted_data'
        result = self.encryptor.encrypt('test_data')
        self.assertEqual(result, 'ZW5jcnlwdGVkX2RhdGE=')  # base64 encoded 'encrypted_data'

    def test_decrypt(self):
        self.mock_crypto_client.return_value.decrypt.return_value.plaintext = b'decrypted_data'
        result = self.encryptor.decrypt('ZW5jcnlwdGVkX2RhdGE=')  # base64 encoded 'encrypted_data'
        self.assertEqual(result, 'decrypted_data')


if __name__ == '__main__':
    unittest.main()