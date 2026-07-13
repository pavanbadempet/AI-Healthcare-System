import uuid


def test_research(client):
    print("[INFO] Testing Super Agent Research...")

    # 1. Signup/Login
    run_id = str(uuid.uuid4())[:8]
    username = f"researcher_{run_id}"
    password = "TestUser123!"
    payload = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "full_name": "Dr. Researcher",
        "dob": "1985-05-05"
    }
    client.post("/signup", json=payload)
    res = client.post("/token", data={"username": username, "password": password})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return

    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Send Research Query (Triggering 'latest' keyword)
    query = {"message": "What is the latest 2024 news on Type 2 Diabetes treatment?", "history": []}
    print(f"   Query: {query['message']}")

    res = client.post("/chat", json=query, headers=headers)

    if res.status_code == 200:
        reply = res.json().get('response', '')
        print(f"   AI Reply: {reply[:200]}...") # Print first 200 chars

        if "http" in reply:
            print("[PASS] AI cited sources (URLs found).")
        else:
            print("[WARN] AI replied but no obvious URLs check if 'latest' triggered Tavily.")
    else:
        print(f"[FAIL] API Error: {res.text}")

