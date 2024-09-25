import unittest
from unittest.mock import patch, MagicMock
import base64
from app import create_app
from app.auth import Auth
from app.cosmos_db_client import CosmosDBClient

class TestAuth(unittest.TestCase):
    @classmethod
    @patch('app.cosmos_db_client.CosmosClient')
    @patch('flask_limiter.Limiter')
    def setUpClass(cls, mock_limiter, mock_cosmos_client):
        test_config = {
            'TESTING': True,
            'API_KEY': 'test_api_key',
            'BASIC_AUTH_USERNAME': 'admin',
            'BASIC_AUTH_PASSWORD': 'admin',
            'COSMOS_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_KEY': 'test_key',
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container'
        }
        cls.app = create_app(test_config)
        cls.auth = Auth(cls.app)

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

class TestCosmosDBClient(unittest.TestCase):
    @patch('app.cosmos_db_client.CosmosClient')
    def setUp(self, mock_cosmos_client):
        self.app = MagicMock()
        self.app.config = {
            'COSMOS_ENDPOINT': 'https://test.documents.azure.com:443/',
            'COSMOS_KEY': 'test_key',
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container'
        }
        self.cosmos_client = CosmosDBClient(self.app)
        self.mock_cosmos_client = mock_cosmos_client

    def test_initialization(self):
        self.mock_cosmos_client.assert_called_once_with(
            'https://test.documents.azure.com:443/',
            credential='test_key'
        )
        self.assertIsNotNone(self.cosmos_client.client)
        self.assertIsNotNone(self.cosmos_client.database)
        self.assertIsNotNone(self.cosmos_client.container)

    def test_get_all_items(self):
        mock_container = self.cosmos_client.container
        mock_items = [
            {'id': '1', 'name': 'Test1'},
            {'id': '2', 'name': 'Test2'}
        ]
        mock_container.query_items.return_value = mock_items
        
        items = self.cosmos_client.get_all_items()
        
        print(f"Type of items: {type(items)}")
        print(f"Content of items: {items}")
        
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 2)
        
        if items and isinstance(items[0], dict):
            self.assertEqual(items[0].get('name'), 'Test1')
            self.assertEqual(items[1].get('name'), 'Test2')
        else:
            self.fail(f"Unexpected structure of items: {items}")


if __name__ == '__main__':
    print("Starting tests...")
    unittest.main(verbosity=2)
    print("Tests complete.")