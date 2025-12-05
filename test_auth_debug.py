import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth():
    print("--- 1. Testing Signup ---")
    try:
        payload = {
            "username": "debug_user_1",
            "password": "password123"
        }
        res = requests.post(f"{BASE_URL}/signup", json=payload)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
        
        if res.status_code != 200:
            print("Signup Failed. check backend logs.")
            return
    except Exception as e:
        print(f"Exeption: {e}")
        return

    print("\n--- 2. Testing Login ---")
    try:
        data = {
            "username": "debug_user_1",
            "password": "password123"
        }
        res = requests.post(f"{BASE_URL}/token", data=data)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_auth()
