import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
    COSMOS_KEY = os.environ.get('COSMOS_KEY')
    DATABASE_NAME = os.environ.get('DATABASE_NAME')
    CONTAINER_NAME = os.environ.get('CONTAINER_NAME')
    API_KEY = os.environ.get('API_KEY')
    RATE_LIMIT = int(os.environ.get('RATE_LIMIT', 100))
    RATE_LIMIT_PERIOD = int(os.environ.get('RATE_LIMIT_PERIOD', 60))
    BASIC_AUTH_USERNAME = os.environ.get('BASIC_AUTH_USERNAME')
    BASIC_AUTH_PASSWORD = os.environ.get('BASIC_AUTH_PASSWORD')

    