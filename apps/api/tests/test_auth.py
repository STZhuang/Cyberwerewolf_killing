"""Test authentication endpoints"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_login_creates_user(client: TestClient):
    """Test that login creates a new user if doesn't exist"""
    response = client.post("/auth/login", json={"username": "newuser"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "token" in data
    assert "user" in data
    assert data["user"]["username"] == "newuser"
    assert data["user"]["banned"] == False


@pytest.mark.unit
def test_login_existing_user(client: TestClient, test_user):
    """Test login with existing user"""
    response = client.post("/auth/login", json={"username": test_user.username})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "token" in data
    assert data["user"]["id"] == test_user.id
    assert data["user"]["username"] == test_user.username


@pytest.mark.unit
def test_get_current_user(client: TestClient, auth_headers):
    """Test getting current user info"""
    response = client.get("/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["username"] == "testuser"
    assert data["banned"] == False


@pytest.mark.unit
def test_unauthorized_access(client: TestClient):
    """Test unauthorized access to protected endpoint"""
    response = client.get("/auth/me")
    
    assert response.status_code == 403  # No Authorization header


@pytest.mark.unit
def test_invalid_token(client: TestClient):
    """Test access with invalid token"""
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.get("/auth/me", headers=headers)
    
    assert response.status_code == 401