def test_signup(client):
    response = client.post(
        "/signup",
        json={
            "username": "testuser",
            "password": "Password1",
            "email": "test@example.com",
            "full_name": "Test User",
            "dob": "1990-01-01"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_login(client):
    # Setup User
    client.post(
        "/signup",
        json={
            "username": "loginuser",
            "password": "Password1",
            "email": "login@example.com",
            "full_name": "Login User",
            "dob": "1990-01-01"
        },
    )
    
    # Login
    response = client.post(
        "/token",
        data={"username": "loginuser", "password": "Password1"},
    )
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

def test_get_profile(client):
    # 1. Signup
    client.post("/signup", json={"username": "prof", "password": "Password1", "email": "p@e.com", "full_name": "P", "dob": "2000-01-01"})
    # 2. Login
    login_res = client.post("/token", data={"username": "prof", "password": "Password1"})
    token = login_res.json()["access_token"]
    
    # 3. Get Profile
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/profile", headers=headers)
    assert res.status_code == 200
    assert res.json()["username"] == "prof"
