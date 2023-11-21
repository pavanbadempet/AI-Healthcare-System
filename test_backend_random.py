import requests
import random
import string

BACKEND_URL = "http://localhost:8000"

def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

username = f"user_{get_random_string(6)}"
password = "testpassword"

print(f"Attempting signup for {username}...")
try:
    res = requests.post(f"{BACKEND_URL}/signup", json={"username": username, "password": password})
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Error: {e}")
