from azure.cosmos import CosmosClient, exceptions
import uuid
import tenacity

class CosmosDBClient:
    def __init__(self, app):
        cosmos_endpoint = app.config.get('COSMOS_ENDPOINT')
        cosmos_key = app.config.get('COSMOS_KEY')
        database_name = app.config.get('DATABASE_NAME')
        container_name = app.config.get('CONTAINER_NAME')
        
        if not all([cosmos_endpoint, cosmos_key, database_name, container_name]):
            raise ValueError("Missing Cosmos DB configuration")
        
        self.client = CosmosClient(cosmos_endpoint, credential=cosmos_key)
        self.database = self.client.get_database_client(database_name)
        self.container = self.database.get_container_client(container_name)

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def get_all_items(self):
        query = "SELECT * FROM c"
        items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
        return items

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def create_item(self, item):
        if 'id' not in item:
            item['id'] = str(uuid.uuid4())
        return self.container.create_item(body=item)

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def get_item(self, id):
        try:
            return self.container.read_item(item=id, partition_key=id)
        except exceptions.CosmosResourceNotFoundError:
            return None

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def update_item(self, item):
        return self.container.upsert_item(body=item)

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type(Exception)
    )
    def delete_item(self, id):
        self.container.delete_item(item=id, partition_key=id)