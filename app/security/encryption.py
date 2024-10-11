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
        self.current_key_version = self._get_latest_key_version()
        self.crypto_client = self._get_crypto_client()

    def _get_latest_key_version(self):
        keys = list(self.key_client.list_properties_of_keys())
        if not keys:
            raise ValueError("No keys found in the key vault")
        latest_key = max(
            (k for k in keys if getattr(k, 'name', None) == self.key_name),
            key=lambda k: getattr(getattr(k, 'properties', None), 'version', '') or ''
        )
        return getattr(getattr(latest_key, 'properties', None), 'version', None)

    def _get_crypto_client(self):
        key = self.key_client.get_key(self.key_name, version=self.current_key_version)
        return CryptographyClient(key, credential=self.credential)

    def encrypt(self, plaintext):
        result = self.crypto_client.encrypt(EncryptionAlgorithm.rsa_oaep, plaintext.encode())
        return f"{base64.b64encode(result.ciphertext).decode()}|{self.current_key_version}"

    def decrypt(self, ciphertext):
        try:
            encrypted_data, _ = ciphertext.rsplit("|", 1)
            result = self.crypto_client.decrypt(EncryptionAlgorithm.rsa_oaep, base64.b64decode(encrypted_data))
            return result.plaintext.decode()
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            return f"[Decryption Error: {str(e)}]"

    def rotate_key(self):
        new_key = self.key_client.create_rsa_key(f"{self.key_name_prefix}-{self.current_key_version + 1}")
        self.current_key_version = new_key.properties.version
        self.crypto_clients[self.current_key_version] = CryptographyClient(new_key, credential=self.credential)
        return self.current_key_version

    def re_encrypt_data(self, data):
        decrypted = self.decrypt(data)
        return self.encrypt(decrypted)
