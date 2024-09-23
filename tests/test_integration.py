import unittest
import json
import sys
import os
from dotenv import load_dotenv
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from azure.cosmos import CosmosClient

load_dotenv() 

class TestFlaskApiUsingCosmosDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_config = {
            'TESTING': True,
            'COSMOS_ENDPOINT': os.getenv('COSMOS_ENDPOINT'),
            'COSMOS_KEY': os.getenv('COSMOS_KEY'),
            'DATABASE_NAME': 'api_client_db',
            'CONTAINER_NAME': 'users',
            'API_KEY': os.getenv('API_KEY'),
            'RATE_LIMIT': 1000,  
            'RATE_LIMIT_PERIOD': 60
        }
        cls.app = create_app(test_config)
        cls.client = cls.app.test_client()
        
        cosmos_client = CosmosClient(cls.app.config['COSMOS_ENDPOINT'], credential=cls.app.config['COSMOS_KEY'])
        database = cosmos_client.get_database_client('api_client_db')
        container = database.get_container_client('users')
        cls.test_item = {'id': 'test_user', 'name': 'Test User', 'email': 'testuser@example.com'}
        container.upsert_item(cls.test_item)

    def setUp(self):
        self.api_key = self.app.config['API_KEY']
        self.basic_auth = base64.b64encode(f"{self.app.config['BASIC_AUTH_USERNAME']}:{self.app.config['BASIC_AUTH_PASSWORD']}".encode()).decode()

    def test_create_item(self):
        new_item = {'name': 'New Test User', 'email': 'newtestuser@example.com'}
        response = self.client.post('/users', 
                                    headers={'X-API-Key': self.api_key, 'Content-Type': 'application/json'},
                                    json=new_item)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertEqual(data['name'], new_item['name'])
        self.assertEqual(data['email'], new_item['email'])

    def test_get_items_api_key(self):
        response = self.client.get('/users', headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    def test_get_items_basic_auth(self):
        response = self.client.get('/users', headers={'Authorization': f'Basic {self.basic_auth}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    def test_update_item(self):
        update_data = {'id': self.test_item['id'], 'name': 'Updated Test User'}
        response = self.client.put(f'/users/{self.test_item["id"]}', 
                                   headers={'X-API-Key': self.api_key, 'Content-Type': 'application/json'},
                                   json=update_data)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], update_data['name'])

    def test_delete_item(self):
        response = self.client.delete(f'/users/{self.test_item["id"]}', headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 204)

    def test_rate_limiting(self):
        for _ in range(101):  
            response = self.client.get('/users', headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 429)

    def test_offset_pagination(self):
        for i in range(15):
            new_item = {'name': f'User {i}', 'email': f'user{i}@example.com'}
            self.client.post('/users', 
                             headers={'X-API-Key': self.api_key, 'Content-Type': 'application/json'},
                             json=new_item)

        response = self.client.get('/users?limit=5&offset=0', headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 5)
        self.assertIn('next_page', data)

        response = self.client.get('/users?limit=5&offset=5', headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 5)
        self.assertIn('next_page', data)

        response = self.client.get('/users?limit=5&offset=10', headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 5)
        self.assertIn('next_page', data)

    def test_cursor_pagination(self):
        for i in range(15):
            new_item = {'name': f'User {i}', 'email': f'user{i}@example.com'}
            self.client.post('/users', 
                             headers={'X-API-Key': self.api_key, 'Content-Type': 'application/json'},
                             json=new_item)

        response = self.client.get('/users?limit=5', headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 5)
        self.assertIn('next_page', data)

        
        next_page_url = data['next_page']
        response = self.client.get(next_page_url, headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 5)
        self.assertIn('next_page', data)

        
        next_page_url = data['next_page']
        response = self.client.get(next_page_url, headers={'X-API-Key': self.api_key})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['users']), 5)
        self.assertIn('next_page', data)

    @classmethod
    def tearDownClass(cls):
        cosmos_client = CosmosClient(cls.app.config['COSMOS_ENDPOINT'], credential=cls.app.config['COSMOS_KEY'])
        database = cosmos_client.get_database_client('api_client_db')
        container = database.get_container_client('users')
        container.delete_item(item=cls.test_item['id'], partition_key=cls.test_item['id'])

if __name__ == '__main__':
    unittest.main()
