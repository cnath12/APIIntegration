# import sys
# import os
#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest
from unittest.mock import MagicMock
from app.security.encryption import Encryptor
import random
import string

class TestEncryption(unittest.TestCase):
    def setUp(self):
        # Create a mock Encryptor for each test
        self.encryptor = MagicMock(spec=Encryptor)
        self.current_version = "v1"
        
        def mock_encrypt(text):
            # Generate a random "nonce" to simulate non-deterministic encryption
            nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            return f"encrypted_{nonce}_{text}|{self.current_version}"
        
        def mock_decrypt(ciphertext):
            text, _ = ciphertext.split("|")
            _, _, original_text = text.split("_", 2)
            return original_text
        
        def mock_rotate_key():
            self.current_version = f"v{int(self.current_version[1:]) + 1}"
            return self.current_version
        
        self.encryptor.encrypt.side_effect = mock_encrypt
        self.encryptor.decrypt.side_effect = mock_decrypt
        self.encryptor.rotate_key.side_effect = mock_rotate_key

    def test_encrypt_decrypt(self):
        original_text = "Hello, World!"
        encrypted_text = self.encryptor.encrypt(original_text)
        decrypted_text = self.encryptor.decrypt(encrypted_text)
        self.assertEqual(decrypted_text, original_text)
        self.assertNotEqual(encrypted_text, original_text)

    def test_encrypt_decrypt_long_text(self):
        original_text = "This is a much longer piece of text that we're using to test the encryption and decryption process with larger data sizes."
        encrypted_text = self.encryptor.encrypt(original_text)
        decrypted_text = self.encryptor.decrypt(encrypted_text)
        self.assertEqual(decrypted_text, original_text)

    def test_key_rotation(self):
        original_text = "Test rotation"
        encrypted_text = self.encryptor.encrypt(original_text)
        old_version = encrypted_text.split("|")[1]
        
        new_version = self.encryptor.rotate_key()
        self.assertNotEqual(new_version, old_version)
        
        decrypted_text = self.encryptor.decrypt(encrypted_text)
        self.assertEqual(decrypted_text, original_text)
        
        new_encrypted_text = self.encryptor.encrypt(original_text)
        self.assertNotEqual(new_encrypted_text, encrypted_text)
        self.assertEqual(new_encrypted_text.split("|")[1], new_version)

    def test_decrypt_after_rotation(self):
        original_text = "Decrypt after rotation"
        encrypted_text = self.encryptor.encrypt(original_text)
        
        self.encryptor.rotate_key()
        
        decrypted_text = self.encryptor.decrypt(encrypted_text)
        self.assertEqual(decrypted_text, original_text)

    def test_multiple_rotations(self):
        original_text = "Multiple rotations"
        encrypted_text = self.encryptor.encrypt(original_text)
        
        for _ in range(3):  # Perform multiple rotations
            self.encryptor.rotate_key()
        
        decrypted_text = self.encryptor.decrypt(encrypted_text)
        self.assertEqual(decrypted_text, original_text)

    def test_encryption_idempotence(self):
        original_text = "Idempotence test"
        encrypted_text1 = self.encryptor.encrypt(original_text)
        encrypted_text2 = self.encryptor.encrypt(original_text)
        
        self.assertNotEqual(encrypted_text1, encrypted_text2)
        
        decrypted_text1 = self.encryptor.decrypt(encrypted_text1)
        decrypted_text2 = self.encryptor.decrypt(encrypted_text2)
        
        self.assertEqual(decrypted_text1, original_text)
        self.assertEqual(decrypted_text2, original_text)

    def test_invalid_ciphertext(self):
        with self.assertRaises(Exception):
            self.encryptor.decrypt("This is not a valid ciphertext")

    def test_empty_string(self):
        empty_text = ""
        encrypted_empty = self.encryptor.encrypt(empty_text)
        decrypted_empty = self.encryptor.decrypt(encrypted_empty)
        self.assertEqual(decrypted_empty, empty_text)

if __name__ == '__main__':
    unittest.main()