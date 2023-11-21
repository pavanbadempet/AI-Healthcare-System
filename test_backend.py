import requests

BACKEND_URL = "http://localhost:8000"

try:
    print("Attempting signup...")
    res = requests.post(f"{BACKEND_URL}/signup", json={"username": "testuser_debug", "password": "testpassword"})
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Error: {e}")
