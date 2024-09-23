# API Integration with Azure Cosmos DB

This project implements a Flask-based REST API that integrates with Azure Cosmos DB. It includes authentication, rate limiting, and CRUD operations for user management.

## Features

- REST API with CRUD operations for users
- Integration with Azure Cosmos DB
- Authentication 
- Rate limiting
- Unit and integration tests

## Prerequisites

- Python 3.7+
- Azure Cosmos DB account

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/APIIntegration.git
   cd APIIntegration
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following content:
   ```
   COSMOS_ENDPOINT=your_cosmos_db_endpoint
   COSMOS_KEY=your_cosmos_db_key
   DATABASE_NAME=your_database_name
   CONTAINER_NAME=your_container_name
   API_KEY=your_api_key
   BASIC_AUTH_USERNAME=your_username
   BASIC_AUTH_PASSWORD=your_password
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   RATE_LIMIT=100
   RATE_LIMIT_PERIOD=60
   ```
   Replace the placeholder values with your actual credentials and settings.

## Running the Application

To run the application:

```
python app.py
```

The API will be available at `http://localhost:5000`.

## Running Tests

To run the unit tests:

```
python -m unittest tests/test_unit.py
```

To run the integration tests:

```
python -m unittest tests/test_integration.py
```

## API Endpoints

- `GET /users`: Get all users
- `POST /users`: Create a new user
- `GET /users/<id>`: Get a specific user
- `PUT /users/<id>`: Update a user
- `DELETE /users/<id>`: Delete a user
- `GET /login/github`: Initiate GitHub OAuth login
- `GET /oauth/callback`: GitHub OAuth callback URL


## Rate Limiting

The API is rate-limited to 100 requests per minute by default. This can be adjusted in the `.env` file.
