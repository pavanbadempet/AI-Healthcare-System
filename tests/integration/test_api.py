import pytest

def test_full_lifecycle(client):
    """
    Simulates a complete user journey:
    1. Register
    2. Login
    3. Post Medical Record
    4. Query Chat (RAG)
    5. Cleanup
    """
    username = "integ_user"
    password = "StrongPassword123!"
    
    # 1. Signup
    res = client.post("/signup", json={
        "username": username,
        "password": password,
        "email": "integ@example.com",
        "full_name": "Integ User",
        "dob": "1990-01-01"
    })
    assert res.status_code == 200
    
    # 2. Login
    res = client.post("/token", data={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Post Record
    rec_payload = {
        "record_type": "Diabetes",
        "data": {"glucose": 95, "bmi": 21.0, "hba1c": 4.8},
        "prediction": "Low Risk"
    }
    res = client.post("/records", json=rec_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    
    # Verify Get
    res = client.get("/records", headers=headers)
    assert res.status_code == 200
    records = res.json()
    assert len(records) == 1
    assert records[0]["prediction"] == "Low Risk"
    
    rec_id = records[0]["id"]
    
    # 4. Chat (RAG Context)
    # Note: RAG might be mocked or we trust the mock_vector_db fixture if scoped correctly.
    # To test integration properly, let's just ensure the endpoint returns valid JSON.
    chat_payload = {
        "message": "Do I have any records?",
        "history": []
    }
    # We expect 200 OK. The content depends on whether the RAG is mocked or real but isolated.
    # tests/conftest.py sets up a separate in-memory sqlite, but RAG uses a file.
    # Ideally integration test would use the mock_vector_db too.
    # Let's see if we can patch it globally or if we need to rely on the file system (which might be messy).
    # Since we can't easily patch inside TestClient requests initiated by the app, 
    # we might just accept that it creates a localized .pkl if we don't mock it.
    
    res = client.post("/chat", json=chat_payload, headers=headers)
    assert res.status_code == 200
    assert "response" in res.json()
    
    # 5. Delete
    res = client.delete(f"/records/{rec_id}", headers=headers)
    assert res.status_code == 200
    
    # Verify Gone
    res = client.get("/records", headers=headers)
    assert len(res.json()) == 0
