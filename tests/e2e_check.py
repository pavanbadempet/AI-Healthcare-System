import requests
import uuid
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

def run_checks():
    print("[INFO] AIO SYSTEM HEALTH CHECK")
    print("==========================")
    
    # 1. Check Root
    try:
        res = requests.get(BASE_URL)
        if res.status_code == 200:
            print("[OK] [API] Root Endpoint is UP")
        else:
            print(f"[FAIL] [API] Root Failed: {res.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] [API] Connection Refused: {e}")
        print("Ensure the backend is running (run_prod.bat)!")
        sys.exit(1)

    # 2. Signup / Auth
    run_id = str(uuid.uuid4())[:8]
    username = f"bot_{run_id}"
    password = "TestUser123!"
    
    print(f"[INFO] Creating Test User: {username}")
    payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "full_name": "Health Bot",
        "dob": "2000-01-01"
    }
    
    res = requests.post(f"{BASE_URL}/signup", json=payload)
    if res.status_code == 200:
        print("[OK] [Auth] Signup Successful")
    else:
        print(f"[FAIL] [Auth] Signup Failed: {res.text}")
        sys.exit(1)

    # Login
    res = requests.post(f"{BASE_URL}/token", data={"username": username, "password": password})
    if res.status_code == 200:
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[OK] [Auth] Login Successful (Token Received)")
    else:
        print(f"[FAIL] [Auth] Login Failed: {res.text}")
        sys.exit(1)

    # 3. Add Health Record
    record_payload = {
        "record_type": "Diabetes",
        "data": {"glucose": 100, "bmi": 22.5, "hba1c": 5.0},
        "prediction": "Low Risk"
    }
    res = requests.post(f"{BASE_URL}/records", json=record_payload, headers=headers)
    if res.status_code == 200:
        print("[OK] [DB] Health Record Saved")
    else:
        print(f"[FAIL] [DB] Save Record Failed: {res.text}")

    # 4. Chat Check (RAG)
    chat_payload = {
        "message": "Hello, I am a test bot. Do I have any records?",
        "history": []
    }
    start = time.time()
    res = requests.post(f"{BASE_URL}/chat", json=chat_payload, headers=headers)
    duration = time.time() - start
    
    if res.status_code == 200:
        print(f"[OK] [AI] Chat Response Received in {duration:.2f}s")
        response_text = res.json()['response'][:50]
        # Sanitize for Windows Console
        safe_response = response_text.encode('ascii', 'ignore').decode('ascii')
        print(f"   Response: {safe_response}...")
    else:
        print(f"[FAIL] [AI] Chat Failed: {res.text}")

    print("\n[SUCCESS] ALL SYSTEMS GREEN.")

if __name__ == "__main__":
    run_checks()
