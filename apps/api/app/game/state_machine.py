"""Game state machine implementation"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class GamePhase(str, Enum):
    """游戏阶段"""
    LOBBY = "Lobby"
    ASSIGN_ROLES = "AssignRoles"
    NIGHT = "Night"
    DAWN = "Dawn"
    DAY_TALK = "DayTalk"
    VOTE = "Vote"
    TRIAL = "Trial"
    DAY_RESULT = "DayResult"
    END = "End"

class GameState:
    """游戏状态"""
    
    def __init__(self, game_id: str, config: Dict[str, Any]):
        self.game_id = game_id
        self.config = config
        self.current_phase = GamePhase.LOBBY
        self.current_round = 0
        self.players: Dict[int, Dict[str, Any]] = {}  # seat -> player_info
        self.phase_start_time: Optional[datetime] = None
        self.phase_deadline: Optional[datetime] = None
        self.votes: Dict[int, Optional[int]] = {}  # voter_seat -> target_seat
        self.night_actions: Dict[int, Dict[str, Any]] = {}  # actor_seat -> action
        self.dead_players: List[int] = []
        self.winner: Optional[str] = None
        
    def get_alive_players(self) -> List[int]:
        """获取存活玩家座位列表"""
        return [seat for seat, player in self.players.items() 
                if player.get("alive", True)]
    
    def get_players_by_role(self, role: str) -> List[int]:
        """获取指定角色的玩家座位列表"""
        return [seat for seat, player in self.players.items() 
                if player.get("role") == role and player.get("alive", True)]
    
    def get_players_by_alignment(self, alignment: str) -> List[int]:
        """获取指定阵营的玩家座位列表"""
        return [seat for seat, player in self.players.items() 
                if player.get("alignment") == alignment and player.get("alive", True)]
    
    def is_game_over(self) -> tuple[bool, Optional[str]]:
        """检查游戏是否结束，返回 (is_over, winner)"""
        alive_werewolves = self.get_players_by_alignment("Werewolf")
        alive_villagers = self.get_players_by_alignment("Village")
        
        if not alive_werewolves:
            return True, "Village"
        elif len(alive_werewolves) >= len(alive_villagers):
            return True, "Werewolf"
        else:
            return False, None

class GameStateMachine:
    """游戏状态机"""
    
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        
    def create_game(self, game_id: str, config: Dict[str, Any]) -> GameState:
        """创建游戏"""
        game_state = GameState(game_id, config)
        self.games[game_id] = game_state
        logger.info(f"Created game {game_id}")
        return game_state
    
    def get_game(self, game_id: str) -> Optional[GameState]:
        """获取游戏状态"""
        return self.games.get(game_id)
    
    def assign_roles(self, game_id: str, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分配角色"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        roles = game.config.get("roles", [])
        if len(players) != len(roles):
            raise ValueError("Player count doesn't match role count")
        
        import random
        random.shuffle(roles)
        
        role_assignments = []
        for i, player in enumerate(players):
            seat = player["seat"]
            role = roles[i]
            alignment = self._get_alignment(role)
            
            game.players[seat] = {
                "user_id": player["user_id"],
                "seat": seat,
                "role": role,
                "alignment": alignment,
                "alive": True,
                "is_bot": player.get("is_bot", False),
                "agent_id": player.get("agent_id")
            }
            
            role_assignments.append({
                "seat": seat,
                "role": role,
                "alignment": alignment
            })
        
        game.current_phase = GamePhase.NIGHT
        game.current_round = 1
        
        logger.info(f"Assigned roles for game {game_id}: {role_assignments}")
        return role_assignments
    
    def start_phase(self, game_id: str, phase: GamePhase, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        """开始新阶段"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        game.current_phase = phase
        game.phase_start_time = datetime.utcnow()
        
        if duration_seconds:
            game.phase_deadline = game.phase_start_time + timedelta(seconds=duration_seconds)
        else:
            # Use default duration from config
            phase_durations = game.config.get("phase_durations", {})
            default_duration = phase_durations.get(phase.value, 60)
            game.phase_deadline = game.phase_start_time + timedelta(seconds=default_duration)
        
        # Clear phase-specific data
        if phase in [GamePhase.VOTE, GamePhase.TRIAL]:
            game.votes.clear()
        elif phase == GamePhase.NIGHT:
            game.night_actions.clear()
        
        logger.info(f"Game {game_id}: Started phase {phase}, deadline {game.phase_deadline}")
        
        return {
            "phase": phase.value,
            "round": game.current_round,
            "deadline": int(game.phase_deadline.timestamp() * 1000) if game.phase_deadline else None,
            "alive_players": game.get_alive_players()
        }
    
    def submit_vote(self, game_id: str, voter_seat: int, target_seat: Optional[int]) -> Dict[str, Any]:
        """提交投票"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.current_phase != GamePhase.VOTE:
            raise ValueError("Not in voting phase")
        
        if voter_seat not in game.get_alive_players():
            raise ValueError("Voter is not alive")
        
        if target_seat is not None and target_seat not in game.get_alive_players():
            raise ValueError("Target is not alive")
        
        game.votes[voter_seat] = target_seat
        
        logger.info(f"Game {game_id}: Player {voter_seat} voted for {target_seat}")
        
        return {
            "voter_seat": voter_seat,
            "target_seat": target_seat,
            "votes": dict(game.votes)
        }
    
    def submit_night_action(
        self, 
        game_id: str, 
        actor_seat: int, 
        action: str, 
        target_seat: Optional[int] = None
    ) -> Dict[str, Any]:
        """提交夜间行动"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if game.current_phase != GamePhase.NIGHT:
            raise ValueError("Not in night phase")
        
        actor = game.players.get(actor_seat)
        if not actor or not actor.get("alive", True):
            raise ValueError("Actor is not alive")
        
        # Validate action based on role
        role = actor.get("role")
        valid_actions = self._get_valid_night_actions(role)
        
        if action not in valid_actions:
            raise ValueError(f"Action {action} not valid for role {role}")
        
        if target_seat is not None and target_seat not in game.get_alive_players():
            raise ValueError("Target is not alive")
        
        game.night_actions[actor_seat] = {
            "action": action,
            "target_seat": target_seat,
            "actor_role": role
        }
        
        logger.info(f"Game {game_id}: Player {actor_seat} ({role}) used {action} on {target_seat}")
        
        return {
            "actor_seat": actor_seat,
            "action": action,
            "target_seat": target_seat
        }
    
    def resolve_vote(self, game_id: str) -> Dict[str, Any]:
        """结算投票"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if not game.votes:
            return {"executed_seat": None, "reason": "no_votes"}
        
        # Count votes
        vote_counts: Dict[Optional[int], int] = {}
        for target in game.votes.values():
            vote_counts[target] = vote_counts.get(target, 0) + 1
        
        # Remove abstentions (None votes) from consideration
        if None in vote_counts:
            del vote_counts[None]
        
        if not vote_counts:
            return {"executed_seat": None, "reason": "all_abstained"}
        
        # Find player(s) with most votes
        max_votes = max(vote_counts.values())
        tied_players = [seat for seat, count in vote_counts.items() if count == max_votes]
        
        if len(tied_players) > 1:
            # Tie - no execution
            return {"executed_seat": None, "reason": "tie", "tied_players": tied_players}
        
        executed_seat = tied_players[0]
        
        # Execute player
        game.players[executed_seat]["alive"] = False
        game.dead_players.append(executed_seat)
        
        logger.info(f"Game {game_id}: Executed player {executed_seat}")
        
        return {
            "executed_seat": executed_seat,
            "reason": "majority",
            "vote_counts": vote_counts
        }
    
    def resolve_night(self, game_id: str) -> Dict[str, Any]:
        """结算夜间行动"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        results = {
            "killed": [],
            "saved": [],
            "poisoned": [],
            "guarded": [],
            "inspected": {}
        }
        
        # Process actions in order: guard -> kill -> save -> poison -> inspect
        guarded_players = set()
        
        # Guard actions
        for actor_seat, action_data in game.night_actions.items():
            if action_data["action"] == "guard" and action_data["target_seat"]:
                guarded_players.add(action_data["target_seat"])
                results["guarded"].append(action_data["target_seat"])
        
        # Kill actions
        kill_targets = set()
        for actor_seat, action_data in game.night_actions.items():
            if action_data["action"] == "kill" and action_data["target_seat"]:
                target = action_data["target_seat"]
                if target not in guarded_players:
                    kill_targets.add(target)
                    results["killed"].append(target)
        
        # Save actions (witch)
        for actor_seat, action_data in game.night_actions.items():
            if action_data["action"] == "save" and action_data["target_seat"]:
                target = action_data["target_seat"]
                if target in kill_targets:
                    kill_targets.remove(target)
                    results["killed"].remove(target)
                    results["saved"].append(target)
        
        # Poison actions (witch)
        for actor_seat, action_data in game.night_actions.items():
            if action_data["action"] == "poison" and action_data["target_seat"]:
                target = action_data["target_seat"]
                if target not in kill_targets:  # Don't double-kill
                    kill_targets.add(target)
                    results["poisoned"].append(target)
        
        # Inspect actions (seer)
        for actor_seat, action_data in game.night_actions.items():
            if action_data["action"] == "inspect" and action_data["target_seat"]:
                target = action_data["target_seat"]
                target_player = game.players.get(target)
                if target_player:
                    results["inspected"][target] = target_player["alignment"]
        
        # Apply deaths
        for seat in kill_targets:
            game.players[seat]["alive"] = False
            game.dead_players.append(seat)
        
        logger.info(f"Game {game_id}: Night results: {results}")
        
        return results
    
    def advance_to_next_phase(self, game_id: str) -> Optional[Dict[str, Any]]:
        """推进到下一阶段"""
        game = self.get_game(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        current_phase = game.current_phase
        
        # Check if game is over
        is_over, winner = game.is_game_over()
        if is_over:
            game.current_phase = GamePhase.END
            game.winner = winner
            return self.start_phase(game_id, GamePhase.END)
        
        # Phase transitions
        if current_phase == GamePhase.LOBBY:
            return self.start_phase(game_id, GamePhase.ASSIGN_ROLES)
        elif current_phase == GamePhase.ASSIGN_ROLES:
            return self.start_phase(game_id, GamePhase.NIGHT)
        elif current_phase == GamePhase.NIGHT:
            return self.start_phase(game_id, GamePhase.DAWN)
        elif current_phase == GamePhase.DAWN:
            return self.start_phase(game_id, GamePhase.DAY_TALK)
        elif current_phase == GamePhase.DAY_TALK:
            return self.start_phase(game_id, GamePhase.VOTE)
        elif current_phase == GamePhase.VOTE:
            return self.start_phase(game_id, GamePhase.TRIAL)
        elif current_phase == GamePhase.TRIAL:
            return self.start_phase(game_id, GamePhase.DAY_RESULT)
        elif current_phase == GamePhase.DAY_RESULT:
            # Start next round
            game.current_round += 1
            return self.start_phase(game_id, GamePhase.NIGHT)
        
        return None
    
    def _get_alignment(self, role: str) -> str:
        """获取角色的阵营"""
        werewolf_roles = {"Werewolf"}
        if role in werewolf_roles:
            return "Werewolf"
        return "Village"
    
    def _get_valid_night_actions(self, role: str) -> List[str]:
        """获取角色的有效夜间行动"""
        role_actions = {
            "Werewolf": ["kill"],
            "Seer": ["inspect"],
            "Witch": ["save", "poison"],
            "Guard": ["guard"],
            "Hunter": [],  # No night action
            "Villager": [],  # No night action
            "Idiot": []  # No night action
        }
        return role_actions.get(role, [])