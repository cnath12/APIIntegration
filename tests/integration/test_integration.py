# import unittest
# import json
# import sys
# import os
# from dotenv import load_dotenv
# import base64

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from app import create_app
# from azure.cosmos import CosmosClient

# load_dotenv() 

# class TestFlaskApiUsingCosmosDB(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         test_config = {
#             'TESTING': True,
#             'COSMOS_ENDPOINT': os.getenv('COSMOS_ENDPOINT'),
#             'DATABASE_NAME': os.getenv('DATABASE_NAME', 'api_client_db'),
#             'CONTAINER_NAME': os.getenv('CONTAINER_NAME', 'users'),
#             'KEY_VAULT_URL': os.getenv('KEY_VAULT_URL'),
#             'KEY_NAME': os.getenv('KEY_NAME'),
#             'API_KEY': os.getenv('API_KEY'),
#             'RATE_LIMIT': 1000,
#             'RATE_LIMIT_PERIOD': 60,
#             'BASIC_AUTH_USERNAME': os.getenv('BASIC_AUTH_USERNAME'),
#             'BASIC_AUTH_PASSWORD': os.getenv('BASIC_AUTH_PASSWORD')
#         }
#         cls.app = create_app(test_config)
#         cls.client = cls.app.test_client()
        
#         cls.cosmos_client = CosmosClient.from_connection_string(os.getenv('COSMOS_CONNECTION_STRING'))
#         cls.database = cls.cosmos_client.get_database_client(test_config['DATABASE_NAME'])
#         cls.container = cls.database.get_container_client(test_config['CONTAINER_NAME'])

#     def setUp(self):
#         self.api_key = self.app.config['API_KEY']
#         if self.app.config.get('BASIC_AUTH_USERNAME') and self.app.config.get('BASIC_AUTH_PASSWORD'):
#             self.basic_auth = base64.b64encode(f"{self.app.config['BASIC_AUTH_USERNAME']}:{self.app.config['BASIC_AUTH_PASSWORD']}".encode()).decode()
#         else:
#             self.basic_auth = None
#         # Create a test item for each test
#         self.test_item = {'id': 'test_user', 'name': 'Test User', 'email': 'testuser@example.com'}
#         self.container.upsert_item(self.test_item)

#     def tearDown(self):
#         # Clean up the test item after each test
#         try:
#             self.container.delete_item(item=self.test_item['id'], partition_key=self.test_item['id'])
#         except:
#             pass

#     def test_create_item(self):
#         new_item = {'name': 'New Test User', 'email': 'newtestuser@example.com'}
#         response = self.client.post('/users', 
#                                     headers={'X-API-Key': self.api_key, 'Content-Type': 'application/json'},
#                                     json=new_item)
#         self.assertEqual(response.status_code, 201)
#         data = json.loads(response.data)
#         self.assertIn('id', data)
#         self.assertEqual(data['name'], new_item['name'])
#         self.assertEqual(data['email'], new_item['email'])
#         # Clean up the created item
#         self.container.delete_item(item=data['id'], partition_key=data['id'])


#     def test_get_items_basic_auth(self):
#         if not self.basic_auth:
#             self.skipTest("Basic auth credentials not set")
#         response = self.client.get('/users', headers={'Authorization': f'Basic {self.basic_auth}'})
#         self.assertEqual(response.status_code, 200)
#         data = json.loads(response.data)
#         self.assertIsInstance(data, dict)
#         self.assertIn('users', data)
#         self.assertIsInstance(data['users'], list)

#     def test_update_item(self):
#         update_data = {'id': self.test_item['id'], 'name': 'Updated Test User'}
#         response = self.client.put(f'/users/{self.test_item["id"]}', 
#                                    headers={'X-API-Key': self.api_key, 'Content-Type': 'application/json'},
#                                    json=update_data)
#         self.assertEqual(response.status_code, 200)
#         data = json.loads(response.data)
#         self.assertEqual(data['name'], update_data['name'])

#     def test_delete_item(self):
#         response = self.client.delete(f'/users/{self.test_item["id"]}', headers={'X-API-Key': self.api_key})
#         self.assertEqual(response.status_code, 204)

# if __name__ == '__main__':
#     unittest.main()
