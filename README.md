# API Integration with Azure Cosmos DB

This project implements various security features for a Flask application, including HTTPS, HSTS, CSP, rate limiting, CRUD operations for user management, and more. It also includes comprehensive testing for encryption, key rotation, and integration with Azure Cosmos DB.

## Features

- REST API with CRUD operations for users
- Secure integration with Azure Cosmos DB
- Multi-factor authentication (API Key, Basic Auth, JWT, OAuth)
- Rate limiting
- Data-in-transit encryption
- Data-at-rest encryption using Azure Key Vault
- Key rotation mechanism for enhanced security
- HTTPS enforcement with TLS 1.3
- Content Security Policy (CSP)
- Strict Transport Security (HSTS)
- Secure cookie settings
- Unit and integration tests

## Prerequisites

- Python 3.7+
- Azure Cosmos DB account
- Azure Key Vault account
- Nginx (for production deployment)

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

### Development
```
python app.py
```

### Production

1. Set up Nginx (refer to the provided Nginx configuration).
2. Run with Gunicorn:
```
./start.sh
```

The API will be available at `http://localhost:5000`.

## Running Tests

To run the unit tests:

```
python -m unittest tests/test_unit.py
```
To run the encryption tests:

```
python -m unittest tests/test_encryption.py
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
- `POST /test_encryption`: Test encryption/decryption
- `GET /test-https`: Test HTTPS configuration

## Security Features

- HTTPS enforcement with TLS 1.3
- Strong cipher suite configuration
- HTTP to HTTPS redirection
- Strict Transport Security (HSTS)
- Content Security Policy (CSP)
- X-Frame-Options, X-Content-Type-Options, and Referrer Policy headers
- Secure cookie settings
- Rate limiting
- Data-at-rest encryption using Azure Key Vault
- Key rotation mechanism for enhanced security
- Multiple authentication methods (API Key, Basic Auth, JWT, OAuth)


## Rate Limiting

The API is rate-limited to 100 requests per minute by default. This can be adjusted in the `.env` file.

## Deployment

The application is configured to run with Gunicorn in production. Use the `start.sh` script to launch the application in a production environment.

## Logging

Application logs are stored in the `logs` directory. Log rotation is implemented to manage log file sizes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request