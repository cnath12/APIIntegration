import unittest
import sys
import os
import base64

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.auth import Auth
from app.cosmos_db_client import CosmosDBClient
from unittest.mock import patch, MagicMock

class TestAuth(unittest.TestCase):
    def setUp(self):
        test_config = {
            'TESTING': True,
            'API_KEY': 'test_api_key',
            'BASIC_AUTH_USERNAME': 'test_user',
            'BASIC_AUTH_PASSWORD': 'test_password',
            'COSMOS_ENDPOINT': 'https://test_endpoint',
            'COSMOS_KEY': base64.b64encode(b'test_key').decode('utf-8'),
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container'
        }
        self.app = create_app(test_config)
        self.auth = Auth(self.app)

    def test_check_api_key(self):
        with self.app.test_request_context(headers={'X-API-Key': 'test_api_key'}):
            self.assertTrue(self.auth.check_api_key())

    def test_check_basic_auth(self):
        with self.app.test_request_context(headers={'Authorization': 'Basic dGVzdF91c2VyOnRlc3RfcGFzc3dvcmQ='}):
            self.assertTrue(self.auth.check_basic_auth())

class TestCosmosDBClient(unittest.TestCase):
    @patch('app.cosmos_db_client.CosmosClient')
    def setUp(self, mock_cosmos_client):
        test_config = {
            'TESTING': True,
            'COSMOS_ENDPOINT': 'https://test_endpoint',
            'COSMOS_KEY': base64.b64encode(b'test_key').decode('utf-8'),
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container'
        }
        self.app = create_app(test_config)
        self.cosmos_client = CosmosDBClient(self.app)
        self.mock_cosmos_client = mock_cosmos_client

    def test_initialization(self):
        self.mock_cosmos_client.assert_called_once_with('https://test_endpoint', credential=base64.b64encode(b'test_key').decode('utf-8'))
        self.assertIsNotNone(self.cosmos_client.client)
        self.assertIsNotNone(self.cosmos_client.database)
        self.assertIsNotNone(self.cosmos_client.container)

if __name__ == '__main__':
    unittest.main()