import requests

api_key = "9btt97YNmLbaofnCwYm79y95TQi9RIBg"
response = requests.get("http://localhost:5000/users", headers={"X-API-Key": api_key})
print(f"API Key Auth Status: {response.status_code}")
print(f"Response: {response.json()}")

username = "admin"
password = "admin"
response = requests.get("http://localhost:5000/users", auth=(username, password))
print(f"Basic Auth Status: {response.status_code}")
print(f"Response: {response.json()}")