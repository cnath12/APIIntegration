import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class Config:
    COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
    DATABASE_NAME = os.environ.get('DATABASE_NAME')
    CONTAINER_NAME = os.environ.get('CONTAINER_NAME')
    RATE_LIMIT = int(os.environ.get('RATE_LIMIT', 1000))
    RATE_LIMIT_PERIOD = int(os.environ.get('RATE_LIMIT_PERIOD', 1000))
    BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
    KEY_VAULT_URL = os.environ.get('KEY_VAULT_URL')
    KEY_NAME = os.environ.get('KEY_NAME')  

    # Common security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600

    @classmethod
    def load_secrets(cls):
        if not cls.KEY_VAULT_URL:
            raise ValueError("KEY_VAULT_URL environment variable is not set")

        credential = DefaultAzureCredential(additionally_allowed_tenants=["*"])
        secret_client = SecretClient(vault_url=cls.KEY_VAULT_URL, credential=credential)

        cls.COSMOS_KEY = secret_client.get_secret('COSMOS-KEY').value
        cls.API_KEY = secret_client.get_secret('API-KEY').value
        cls.BASIC_AUTH_PASSWORD = secret_client.get_secret('BASIC-AUTH-PASSWORD').value
        cls.GITHUB_CLIENT_ID = secret_client.get_secret('GITHUB-CLIENT-ID').value
        cls.GITHUB_CLIENT_SECRET = secret_client.get_secret('GITHUB-CLIENT-SECRET').value
        cls.JWT_SECRET_KEY = secret_client.get_secret('JWT-SECRET-KEY').value
        cls.SECRET_KEY = secret_client.get_secret('SECRET-KEY').value

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    # SESSION_COOKIE_HTTPONLY = True
    # SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    TESTING = True
    SESSION_COOKIE_SECURE = False
    @classmethod
    def load_secrets(cls):
        print(f"Attempting to load secrets from Key Vault URL: {cls.KEY_VAULT_URL}")
        if not cls.KEY_VAULT_URL:
            raise ValueError("KEY_VAULT_URL environment variable is not set")

        try:
            credential = DefaultAzureCredential(additionally_allowed_tenants=["*"])
            secret_client = SecretClient(vault_url=cls.KEY_VAULT_URL, credential=credential)

            secrets_to_load = {
                'COSMOS-KEY': 'COSMOS_KEY',
                'API-KEY': 'API_KEY',
                'BASIC-AUTH-PASSWORD': 'BASIC_AUTH_PASSWORD',
                'GITHUB-CLIENT-ID': 'GITHUB_CLIENT_ID',
                'GITHUB-CLIENT-SECRET': 'GITHUB_CLIENT_SECRET',
                'JWT-SECRET-KEY': 'JWT_SECRET_KEY',
                'SECRET-KEY': 'SECRET_KEY'
            }
            
            for secret_name, attr_name in secrets_to_load.items():
                try:
                    value = secret_client.get_secret(secret_name).value
                    setattr(cls, attr_name, value)
                    print(f"Successfully loaded secret: {secret_name}")
                except Exception as e:
                    print(f"Failed to load secret {secret_name}: {str(e)}")

        except Exception as e:
            print(f"Error loading secrets from Key Vault: {str(e)}")
            raise

def get_config():
    env = os.environ.get('FLASK_ENV', 'testing').lower()
    if env == 'production':
        print("Using ProductionConfig")
        return ProductionConfig
    elif env == 'testing':
        print("Using TestingConfig")
        return TestingConfig
    else:
        print("Using DevelopmentConfig")
        return DevelopmentConfig