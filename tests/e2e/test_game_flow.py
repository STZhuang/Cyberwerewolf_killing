"""End-to-end game flow tests"""

import pytest
import asyncio
from fastapi.testclient import TestClient


@pytest.mark.e2e
@pytest.mark.slow
def test_complete_game_flow(client: TestClient):
    """Test a complete game from creation to end"""
    
    # Step 1: Create users
    users = []
    for i in range(6):  # Minimum players for game
        response = client.post("/auth/login", json={"username": f"player{i+1}"})
        assert response.status_code == 200
        token = response.json()["token"]
        users.append({
            "username": f"player{i+1}",
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        })
    
    # Step 2: Create room
    room_data = {
        "max_players": 6,
        "config": {
            "roles": ["Villager", "Villager", "Villager", "Werewolf", "Werewolf", "Seer"],
            "phase_durations": {"Night": 5, "DayTalk": 10, "Vote": 5, "Trial": 3}
        }
    }
    
    response = client.post("/rooms/", json=room_data, headers=users[0]["headers"])
    assert response.status_code == 200
    room = response.json()
    
    # Step 3: Join room with all users
    for user in users[1:]:  # First user is already in room
        response = client.post(f"/rooms/{room['id']}/join", headers=user["headers"])
        assert response.status_code == 200
    
    # Step 4: Verify room is full
    response = client.get(f"/rooms/{room['id']}")
    assert response.status_code == 200
    room_details = response.json()
    assert len(room_details["members"]) == 6
    
    # Step 5: Start game
    response = client.post(f"/rooms/{room['id']}/start", headers=users[0]["headers"])
    assert response.status_code == 200
    game_result = response.json()
    
    assert "game_id" in game_result
    assert "assignments" in game_result
    assert len(game_result["assignments"]) == 6
    
    # Verify all required roles are assigned
    assigned_roles = [a["role"] for a in game_result["assignments"]]
    expected_roles = room_data["config"]["roles"]
    assert sorted(assigned_roles) == sorted(expected_roles)
    
    # Verify alignments are correct
    for assignment in game_result["assignments"]:
        role = assignment["role"]
        alignment = assignment["alignment"]
        
        if role == "Werewolf":
            assert alignment == "Werewolf"
        else:
            assert alignment == "Village"


@pytest.mark.e2e
def test_room_management_flow(client: TestClient):
    """Test complete room management flow"""
    
    # Create host user
    response = client.post("/auth/login", json={"username": "host"})
    host_token = response.json()["token"]
    host_headers = {"Authorization": f"Bearer {host_token}"}
    
    # Create guest user
    response = client.post("/auth/login", json={"username": "guest"})
    guest_token = response.json()["token"]
    guest_headers = {"Authorization": f"Bearer {guest_token}"}
    
    # Create room
    room_data = {"max_players": 4}
    response = client.post("/rooms/", json=room_data, headers=host_headers)
    assert response.status_code == 200
    room = response.json()
    
    # Guest joins room
    response = client.post(f"/rooms/{room['id']}/join", headers=guest_headers)
    assert response.status_code == 200
    join_result = response.json()
    assert "seat" in join_result
    
    # Verify room has 2 members
    response = client.get(f"/rooms/{room['id']}")
    assert response.status_code == 200
    room_details = response.json()
    assert len(room_details["members"]) == 2
    
    # Guest leaves room
    response = client.post(f"/rooms/{room['id']}/leave", headers=guest_headers)
    assert response.status_code == 200
    
    # Verify room has 1 member
    response = client.get(f"/rooms/{room['id']}")
    assert response.status_code == 200
    room_details = response.json()
    assert len(room_details["members"]) == 1
    
    # Guest tries to join again
    response = client.post(f"/rooms/{room['id']}/join", headers=guest_headers)
    assert response.status_code == 200


@pytest.mark.e2e
def test_error_handling_flow(client: TestClient):
    """Test various error scenarios"""
    
    # Create user
    response = client.post("/auth/login", json={"username": "testuser"})
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to join nonexistent room
    response = client.post("/rooms/nonexistent-id/join", headers=headers)
    assert response.status_code == 404
    
    # Try to get nonexistent room
    response = client.get("/rooms/nonexistent-id")
    assert response.status_code == 404
    
    # Try to start game in nonexistent room
    response = client.post("/rooms/nonexistent-id/start", headers=headers)
    assert response.status_code == 404
    
    # Create room
    room_data = {"max_players": 2}
    response = client.post("/rooms/", json=room_data, headers=headers)
    assert response.status_code == 200
    room = response.json()
    
    # Try to start game with insufficient players
    response = client.post(f"/rooms/{room['id']}/start", headers=headers)
    assert response.status_code == 409  # Need at least 6 players
    
    # Try to access protected endpoint without auth
    response = client.post("/rooms/")
    assert response.status_code == 403