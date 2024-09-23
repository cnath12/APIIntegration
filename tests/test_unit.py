import unittest
from app import create_app
from app.auth import Auth
from app.rate_limiter import RateLimiter
from app.cosmos_db_client import CosmosDBClient
from unittest.mock import patch, MagicMock

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True)
        self.app.config['API_KEY'] = 'test_api_key'
        self.app.config['BASIC_AUTH_USERNAME'] = 'test_user'
        self.app.config['BASIC_AUTH_PASSWORD'] = 'test_password'
        self.auth = Auth(self.app)

    def test_check_api_key(self):
        with self.app.test_request_context(headers={'X-API-Key': 'test_api_key'}):
            self.assertTrue(self.auth.check_api_key())

    def test_check_basic_auth(self):
        with self.app.test_request_context(headers={'Authorization': 'Basic dGVzdF91c2VyOnRlc3RfcGFzc3dvcmQ='}):
            self.assertTrue(self.auth.check_basic_auth())

class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True)
        self.app.config['RATE_LIMIT'] = 5
        self.app.config['RATE_LIMIT_PERIOD'] = 60
        self.rate_limiter = RateLimiter(self.app)

    def test_rate_limit(self):
        with self.app.test_request_context():
            for _ in range(5):
                self.assertIsNone(self.rate_limiter.limit()(lambda: None)())
            response = self.rate_limiter.limit()(lambda: None)()
            self.assertEqual(response[1], 429)  # HTTP 429 Too Many Requests

class TestCosmosDBClient(unittest.TestCase):
    def setUp(self):
        self.app = create_app(testing=True)
        self.app.config['COSMOS_ENDPOINT'] = 'https://test_endpoint'
        self.app.config['COSMOS_KEY'] = 'test_key'
        self.app.config['DATABASE_NAME'] = 'test_db'
        self.app.config['CONTAINER_NAME'] = 'test_container'
        self.cosmos_client = CosmosDBClient(self.app)

    @patch('app.cosmos_db_client.CosmosClient')
    def test_initialization(self, mock_cosmos_client):
        # Create a new app with mocked config
        app = MagicMock()
        app.config = {
            'TESTING': False,
            'COSMOS_ENDPOINT': 'https://test_endpoint',
            'COSMOS_KEY': 'test_key',
            'DATABASE_NAME': 'test_db',
            'CONTAINER_NAME': 'test_container'
        }

        cosmos_client = CosmosDBClient(app)
        
        mock_cosmos_client.assert_called_once_with('https://test_endpoint', credential='test_key')
        
        self.assertIsNotNone(cosmos_client.client)
        self.assertIsNotNone(cosmos_client.database)
        self.assertIsNotNone(cosmos_client.container)

if __name__ == '__main__':
    unittest.main()