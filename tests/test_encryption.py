import unittest
from unittest.mock import Mock, patch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)

from app.encryption import Encryptor

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