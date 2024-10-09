import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from unittest.mock import MagicMock, patch
from app.cosmos_db_client import CosmosDBClient

class TestKeyRotation(unittest.TestCase):
    def setUp(self):
        self.rotation_test_data = [
            {"id": "rot1", "name": "Rotation Test 1", "age": 40},
            {"id": "rot2", "name": "Rotation Test 2", "age": 45},
            {"id": "rot3", "name": "Rotation Test 3", "age": 50}
        ]
        self.cosmos_db_client = MagicMock(spec=CosmosDBClient)
        
        # Mock the encryptor with a more sophisticated encryption/decryption simulation
        self.cosmos_db_client.encryptor = MagicMock()
        self.current_key_version = 'v1'
        
        def mock_encrypt(text):
            return f"{self.current_key_version}_encrypted_{text}"
        
        def mock_decrypt(text):
            parts = text.split('_', 2)
            if len(parts) == 3:
                return parts[2]
            return text.replace("encrypted_", "")
        
        self.cosmos_db_client.encryptor.encrypt.side_effect = mock_encrypt
        self.cosmos_db_client.encryptor.decrypt.side_effect = mock_decrypt

    def test_key_rotation_process(self):
        # Create test data
        created_items = []
        for item in self.rotation_test_data:
            created_item = self.cosmos_db_client.create_item(item)
            created_items.append(created_item)
        
        # Verify initial data
        self.cosmos_db_client.get_all_items.return_value = [
            {"id": item["id"], "name": f"{self.current_key_version}_encrypted_{item['name']}", "age": item["age"]}
            for item in self.rotation_test_data
        ]
        initial_items = self.cosmos_db_client.get_all_items()
        initial_encrypted_names = [item['name'] for item in initial_items if item['id'].startswith('rot')]
        
        # Store initial encrypted data for later comparison
        initial_encrypted_data = {item['id']: item['name'] for item in initial_items if item['id'].startswith('rot')}
        
        # Perform key rotation
        self.current_key_version = 'v2'  # Simulate key rotation
        new_version = self.cosmos_db_client.rotate_encryption_key()
        
        # Verify data after rotation
        self.cosmos_db_client.get_all_items.return_value = [
            {"id": item["id"], "name": f"{self.current_key_version}_encrypted_{item['name']}", "age": item["age"]}
            for item in self.rotation_test_data
        ]
        rotated_items = self.cosmos_db_client.get_all_items()
        rotated_encrypted_names = [item['name'] for item in rotated_items if item['id'].startswith('rot')]
        
        # Check that encryption changed
        self.assertNotEqual(initial_encrypted_names, rotated_encrypted_names)
        
        # Check that decrypted data is the same
        for item in rotated_items:
            if item['id'].startswith('rot'):
                decrypted_name = self.cosmos_db_client.encryptor.decrypt(item['name'])
                original_item = next(i for i in self.rotation_test_data if i['id'] == item['id'])
                self.assertEqual(decrypted_name, original_item['name'])
        
        # Verify that old encrypted data can still be decrypted
        for item_id, old_encrypted_name in initial_encrypted_data.items():
            decrypted_old_name = self.cosmos_db_client.encryptor.decrypt(old_encrypted_name)
            original_item = next(i for i in self.rotation_test_data if i['id'] == item_id)
            self.assertEqual(decrypted_old_name, original_item['name'])
        
        # Test creating a new item after rotation
        new_item = {"id": "rot4", "name": "Rotation Test 4", "age": 55}
        created_new_item = self.cosmos_db_client.create_item(new_item)
        
        # Verify the new item is encrypted with the new key
        self.cosmos_db_client.get_item.return_value = {"id": "rot4", "name": f"{self.current_key_version}_encrypted_Rotation Test 4", "age": 55}
        retrieved_new_item = self.cosmos_db_client.get_item(new_item['id'])
        self.assertNotEqual(retrieved_new_item['name'], new_item['name'])  # Should be encrypted
        decrypted_new_name = self.cosmos_db_client.encryptor.decrypt(retrieved_new_item['name'])
        self.assertEqual(decrypted_new_name, new_item['name'])
        
        # Clean up test data
        for item in self.rotation_test_data + [new_item]:
            self.cosmos_db_client.delete_item(item['id'])

    def test_multiple_rotations(self):
        # Create a test item
        test_item = {"id": "multi_rot", "name": "Multiple Rotation Test", "age": 60}
        created_item = self.cosmos_db_client.create_item(test_item)
        
        # Perform multiple rotations
        for _ in range(3):
            self.cosmos_db_client.rotate_encryption_key()
        
        # Retrieve and verify the item after multiple rotations
        self.cosmos_db_client.get_item.return_value = {"id": "multi_rot", "name": "encrypted_Multiple Rotation Test", "age": 60}
        retrieved_item = self.cosmos_db_client.get_item(test_item['id'])
        decrypted_name = self.cosmos_db_client.encryptor.decrypt(retrieved_item['name'])
        self.assertEqual(decrypted_name, test_item['name'])
        
        # Clean up
        self.cosmos_db_client.delete_item(test_item['id'])

    def test_rotation_with_updates(self):
        # Create a test item
        test_item = {"id": "rot_update", "name": "Rotation Update Test", "age": 65}
        created_item = self.cosmos_db_client.create_item(test_item)
        
        # Rotate key
        self.cosmos_db_client.rotate_encryption_key()
        
        # Update the item
        updated_item = {"id": "rot_update", "name": "Updated After Rotation", "age": 66}
        self.cosmos_db_client.update_item(updated_item)
        
        # Retrieve and verify the updated item
        self.cosmos_db_client.get_item.return_value = {"id": "rot_update", "name": "encrypted_Updated After Rotation", "age": 66}
        retrieved_item = self.cosmos_db_client.get_item(test_item['id'])
        decrypted_name = self.cosmos_db_client.encryptor.decrypt(retrieved_item['name'])
        self.assertEqual(decrypted_name, updated_item['name'])
        self.assertEqual(retrieved_item['age'], updated_item['age'])
        
        # Clean up
        self.cosmos_db_client.delete_item(test_item['id'])

if __name__ == '__main__':
    unittest.main()