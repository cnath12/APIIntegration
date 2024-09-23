import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, exceptions

load_dotenv()

def test_connection():
    try:
        client = CosmosClient(os.getenv('COSMOS_ENDPOINT'), credential=os.getenv('COSMOS_KEY'))
        database = client.get_database_client(os.getenv('DATABASE_NAME'))
        container = database.get_container_client(os.getenv('CONTAINER_NAME'))
        
        items = list(container.read_all_items(max_item_count=100))
        print(f"Successfully connected to Cosmos DB. Found {len(items)} items.")
        return True
    except exceptions.CosmosHttpResponseError as e:
        print(f"Failed to connect to Cosmos DB: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()