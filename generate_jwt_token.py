import os
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

# Load environment variables
load_dotenv()

# Create a minimal Flask app
app = Flask(__name__)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')

# Check if JWT_SECRET_KEY is set
if not app.config['JWT_SECRET_KEY']:
    raise ValueError("JWT_SECRET_KEY is not set in the .env file")

# Initialize JWTManager
jwt = JWTManager(app)

def generate_token(username, expiration_minutes=30):
    """
    Generate a JWT token for the given username.
    
    :param username: The username to include in the token
    :param expiration_minutes: Token expiration time in minutes (default: 30)
    :return: JWT token as a string
    """
    with app.app_context():
        expires = timedelta(minutes=expiration_minutes)
        token = create_access_token(identity=username, expires_delta=expires)
        return token

if __name__ == "__main__":
    # Example usage
    username = input("Enter username: ")
    token = generate_token(username)
    print(f"\nGenerated JWT token for {username}:")
    print(token)
    