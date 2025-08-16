"""Test game state machine"""

import pytest
from datetime import datetime

from app.game.state_machine import GameStateMachine, GamePhase


@pytest.mark.unit
def test_create_game():
    """Test game creation"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-1"
    config = {
        "roles": ["Villager", "Werewolf", "Seer"],
        "phase_durations": {"Night": 30, "DayTalk": 60, "Vote": 30}
    }
    
    game_state = state_machine.create_game(game_id, config)
    
    assert game_state.game_id == game_id
    assert game_state.config == config
    assert game_state.current_phase == GamePhase.LOBBY
    assert game_state.current_round == 0


@pytest.mark.unit
def test_assign_roles():
    """Test role assignment"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-2"
    config = {"roles": ["Villager", "Werewolf", "Seer"]}
    
    state_machine.create_game(game_id, config)
    
    players = [
        {"seat": 1, "user_id": "user1"},
        {"seat": 2, "user_id": "user2"},
        {"seat": 3, "user_id": "user3"}
    ]
    
    assignments = state_machine.assign_roles(game_id, players)
    
    assert len(assignments) == 3
    assert all("seat" in assignment for assignment in assignments)
    assert all("role" in assignment for assignment in assignments)
    assert all("alignment" in assignment for assignment in assignments)
    
    # Check that all roles are assigned
    assigned_roles = [a["role"] for a in assignments]
    assert set(assigned_roles) == set(config["roles"])


@pytest.mark.unit
def test_submit_vote():
    """Test vote submission"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-3"
    config = {"roles": ["Villager", "Werewolf"]}
    
    game_state = state_machine.create_game(game_id, config)
    
    # Set up players
    game_state.players = {
        1: {"alive": True},
        2: {"alive": True}
    }
    
    # Start vote phase
    state_machine.start_phase(game_id, GamePhase.VOTE)
    
    # Submit vote
    result = state_machine.submit_vote(game_id, 1, 2)
    
    assert result["voter_seat"] == 1
    assert result["target_seat"] == 2
    assert 1 in result["votes"]
    assert result["votes"][1] == 2


@pytest.mark.unit
def test_resolve_vote_majority():
    """Test vote resolution with clear majority"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-4"
    config = {"roles": ["Villager", "Villager", "Werewolf"]}
    
    game_state = state_machine.create_game(game_id, config)
    
    # Set up players
    game_state.players = {
        1: {"alive": True},
        2: {"alive": True},
        3: {"alive": True}
    }
    
    # Set up votes (1 and 2 vote for 3)
    game_state.votes = {1: 3, 2: 3, 3: 1}
    
    result = state_machine.resolve_vote(game_id)
    
    assert result["executed_seat"] == 3
    assert result["reason"] == "majority"
    assert not game_state.players[3]["alive"]


@pytest.mark.unit
def test_resolve_vote_tie():
    """Test vote resolution with tie"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-5"
    config = {"roles": ["Villager", "Villager"]}
    
    game_state = state_machine.create_game(game_id, config)
    
    # Set up players
    game_state.players = {
        1: {"alive": True},
        2: {"alive": True}
    }
    
    # Set up tie votes
    game_state.votes = {1: 2, 2: 1}
    
    result = state_machine.resolve_vote(game_id)
    
    assert result["executed_seat"] is None
    assert result["reason"] == "tie"


@pytest.mark.unit
def test_night_action_kill():
    """Test werewolf night kill action"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-6"
    config = {"roles": ["Villager", "Werewolf"]}
    
    game_state = state_machine.create_game(game_id, config)
    
    # Set up players
    game_state.players = {
        1: {"alive": True, "role": "Villager", "alignment": "Village"},
        2: {"alive": True, "role": "Werewolf", "alignment": "Werewolf"}
    }
    
    # Start night phase
    state_machine.start_phase(game_id, GamePhase.NIGHT)
    
    # Submit kill action
    result = state_machine.submit_night_action(game_id, 2, "kill", 1)
    
    assert result["actor_seat"] == 2
    assert result["action"] == "kill"
    assert result["target_seat"] == 1


@pytest.mark.unit
def test_resolve_night_kill():
    """Test night resolution with kill"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-7"
    config = {"roles": ["Villager", "Werewolf"]}
    
    game_state = state_machine.create_game(game_id, config)
    
    # Set up players
    game_state.players = {
        1: {"alive": True},
        2: {"alive": True}
    }
    
    # Set up night action
    game_state.night_actions = {
        2: {"action": "kill", "target_seat": 1, "actor_role": "Werewolf"}
    }
    
    result = state_machine.resolve_night(game_id)
    
    assert 1 in result["killed"]
    assert not game_state.players[1]["alive"]


@pytest.mark.unit
def test_game_over_detection():
    """Test game over detection"""
    state_machine = GameStateMachine()
    
    game_id = "test-game-8"
    config = {"roles": ["Villager", "Werewolf"]}
    
    game_state = state_machine.create_game(game_id, config)
    
    # Set up players - werewolf wins scenario
    game_state.players = {
        1: {"alive": False, "alignment": "Village"},
        2: {"alive": True, "alignment": "Werewolf"}
    }
    
    is_over, winner = game_state.is_game_over()
    
    assert is_over is True
    assert winner == "Werewolf"