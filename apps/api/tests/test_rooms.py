"""Test room management endpoints"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_create_room(client: TestClient, auth_headers):
    """Test creating a new room"""
    room_data = {
        "max_players": 9,
        "config": {
            "roles": ["Villager", "Villager", "Werewolf", "Werewolf", "Seer"],
            "phase_durations": {"Night": 30, "DayTalk": 120, "Vote": 30}
        }
    }
    
    response = client.post("/rooms/", json=room_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert "code" in data
    assert len(data["code"]) == 4
    assert data["status"] == "open"
    assert data["max_players"] == 9
    assert len(data["members"]) == 1  # Creator is first member


@pytest.mark.unit
def test_list_rooms(client: TestClient, test_room):
    """Test listing rooms"""
    response = client.get("/rooms/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(room["id"] == test_room["id"] for room in data)


@pytest.mark.unit
def test_get_room_details(client: TestClient, test_room):
    """Test getting room details"""
    response = client.get(f"/rooms/{test_room['id']}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == test_room["id"]
    assert data["code"] == test_room["code"]
    assert data["status"] == "open"


@pytest.mark.unit
def test_join_room(client: TestClient, test_room):
    """Test joining a room"""
    # Create another user
    login_response = client.post("/auth/login", json={"username": "player2"})
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Join the room
    response = client.post(f"/rooms/{test_room['id']}/join", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Successfully joined room"
    assert "seat" in data


@pytest.mark.unit
def test_join_nonexistent_room(client: TestClient, auth_headers):
    """Test joining a nonexistent room"""
    response = client.post("/rooms/nonexistent/join", headers=auth_headers)
    
    assert response.status_code == 404


@pytest.mark.unit
def test_leave_room(client: TestClient, test_room, auth_headers):
    """Test leaving a room"""
    response = client.post(f"/rooms/{test_room['id']}/leave", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Successfully left room"


@pytest.mark.unit
def test_unauthorized_room_access(client: TestClient):
    """Test unauthorized access to room endpoints"""
    response = client.post("/rooms/")
    
    assert response.status_code == 403  # No auth header