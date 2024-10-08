from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, EncryptionAlgorithm
from azure.identity import DefaultAzureCredential
import base64

class Encryptor:
    def __init__(self, key_vault_url, key_name):
        self.key_vault_url = key_vault_url
        self.key_name = key_name
        self.credential = DefaultAzureCredential()
        self.key_client = KeyClient(vault_url=key_vault_url, credential=self.credential)
        self.crypto_client = self._get_crypto_client()

    def _get_crypto_client(self):
        key = self.key_client.get_key(self.key_name)
        return CryptographyClient(key, credential=self.credential)

    def encrypt(self, plaintext):
        result = self.crypto_client.encrypt(EncryptionAlgorithm.rsa_oaep, plaintext.encode())
        return base64.b64encode(result.ciphertext).decode()

    def decrypt(self, ciphertext):
        try:
            if isinstance(ciphertext, str):
                ciphertext = base64.b64decode(ciphertext)
            result = self.crypto_client.decrypt(EncryptionAlgorithm.rsa_oaep, ciphertext)
            return result.plaintext.decode()
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            return f"[Decryption Error: {str(e)}]"