"""Test agent context builder"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from app.agent.context_builder import AgentContextBuilder
from app.game.state_machine import GameStateMachine, GamePhase


@pytest.mark.unit
def test_build_observation(db_session):
    """Test building agent observation"""
    state_machine = GameStateMachine()
    context_builder = AgentContextBuilder(db_session, state_machine)
    
    # Create game state
    game_id = "test-game"
    config = {
        "roles": ["Villager", "Werewolf", "Seer"],
        "phase_durations": {"Night": 30, "DayTalk": 60}
    }
    
    game_state = state_machine.create_game(game_id, config)
    
    # Set up players
    game_state.players = {
        1: {"seat": 1, "role": "Seer", "alignment": "Village", "alive": True},
        2: {"seat": 2, "role": "Werewolf", "alignment": "Werewolf", "alive": True},
        3: {"seat": 3, "role": "Villager", "alignment": "Village", "alive": True}
    }
    
    game_state.current_phase = GamePhase.DAY_TALK
    game_state.current_round = 1
    game_state.phase_deadline = datetime.utcnow()
    
    # Build observation for seer
    observation = context_builder.build_observation(game_id, 1)
    
    # Check game info
    assert observation.game_info.game_id == game_id
    assert observation.game_info.round == 1
    assert observation.game_info.phase == GamePhase.DAY_TALK
    
    # Check self info
    assert observation.self.seat == 1
    assert observation.self.role == "Seer"
    assert observation.self.alive is True
    
    # Check public state
    assert observation.public_state.player_count == 3
    assert set(observation.public_state.alive_seats) == {1, 2, 3}


@pytest.mark.unit
def test_get_allowed_actions(db_session):
    """Test getting allowed actions for different phases"""
    state_machine = GameStateMachine()
    context_builder = AgentContextBuilder(db_session, state_machine)
    
    # Create game state
    game_id = "test-game"
    game_state = state_machine.create_game(game_id, {})
    
    # Set up werewolf player
    game_state.players = {
        1: {"seat": 1, "role": "Werewolf", "alignment": "Werewolf", "alive": True}
    }
    
    # Test night phase actions
    game_state.current_phase = GamePhase.NIGHT
    actions = context_builder.get_allowed_actions(game_id, 1)
    
    assert "say" in actions
    assert "night_action_kill" in actions
    assert "ask_gm_for_clarification" in actions
    
    # Test vote phase actions
    game_state.current_phase = GamePhase.VOTE
    actions = context_builder.get_allowed_actions(game_id, 1)
    
    assert "say" in actions
    assert "vote" in actions
    assert "night_action_kill" not in actions


@pytest.mark.unit
def test_action_constraints(db_session):
    """Test getting action constraints"""
    state_machine = GameStateMachine()
    context_builder = AgentContextBuilder(db_session, state_machine)
    
    # Create game state
    game_id = "test-game"
    game_state = state_machine.create_game(game_id, {})
    
    # Set up players
    game_state.players = {
        1: {"seat": 1, "role": "Werewolf", "alignment": "Werewolf", "alive": True},
        2: {"seat": 2, "role": "Villager", "alignment": "Village", "alive": True},
        3: {"seat": 3, "role": "Werewolf", "alignment": "Werewolf", "alive": True}
    }
    
    game_state.current_phase = GamePhase.NIGHT
    
    constraints = context_builder.get_action_constraints(game_id, 1)
    
    # Werewolf can't kill other werewolves
    assert "kill_targets" in constraints
    assert 2 in constraints["kill_targets"]  # Can kill villager
    assert 3 not in constraints["kill_targets"]  # Can't kill other werewolf


@pytest.mark.unit
def test_information_isolation(db_session):
    """Test that sensitive information is properly isolated"""
    state_machine = GameStateMachine()
    context_builder = AgentContextBuilder(db_session, state_machine)
    
    # Create game state
    game_id = "test-game"
    game_state = state_machine.create_game(game_id, {})
    
    # Set up players with hidden information
    game_state.players = {
        1: {"seat": 1, "role": "Villager", "alignment": "Village", "alive": True},
        2: {"seat": 2, "role": "Werewolf", "alignment": "Werewolf", "alive": True}
    }
    
    # Build observation for villager
    observation = context_builder.build_observation(game_id, 1)
    
    # Villager should only know their own role
    assert observation.self.role == "Villager"
    
    # Should not have access to other players' roles in public state
    # (only revealed/dead players should show roles)
    assert len(observation.public_state.revealed_identities) == 0