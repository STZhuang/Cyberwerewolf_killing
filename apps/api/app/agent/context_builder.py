"""Agent context builder - implements D03 specification for information isolation"""

# Configure Python path for SDK imports
from app.path_config import *

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.database import Game, GamePlayer, Event
from app.game.state_machine import GameStateMachine
from cyber_werewolves.models.agent_models import (
    AgentObservation, GameInfo, SelfInfo, PublicState, 
    ChatHistory, ChatMessage, PrivateNote
)

logger = logging.getLogger(__name__)

class AgentContextBuilder:
    """构建Agent可见上下文 - 严格信息隔离"""
    
    def __init__(self, db: Session, state_machine: GameStateMachine):
        self.db = db
        self.state_machine = state_machine
    
    def build_observation(self, game_id: str, seat: int) -> AgentObservation:
        """为指定座位构建可见观察上下文"""
        
        # Get game state
        game_state = self.state_machine.get_game(game_id)
        if not game_state:
            raise ValueError("Game not found")
        
        # Get player info
        player = game_state.players.get(seat)
        if not player:
            raise ValueError("Player not found")
        
        # Build each component
        game_info = self._build_game_info(game_state)
        self_info = self._build_self_info(player)
        public_state = self._build_public_state(game_state)
        chat_history = self._build_chat_history(game_id, seat, player)
        private_notes = self._build_private_notes(game_id, seat)
        
        return AgentObservation(
            game_info=game_info,
            self=self_info,
            public_state=public_state,
            chat_history=chat_history,
            private_notes=private_notes
        )
    
    def _build_game_info(self, game_state) -> GameInfo:
        """构建游戏基础信息"""
        deadline_ts = None
        if game_state.phase_deadline:
            deadline_ts = int(game_state.phase_deadline.timestamp() * 1000)
        
        return GameInfo(
            game_id=game_state.game_id,
            round=game_state.current_round,
            phase=game_state.current_phase,
            phase_deadline_ts=deadline_ts
        )
    
    def _build_self_info(self, player: Dict[str, Any]) -> SelfInfo:
        """构建自身信息"""
        status = {
            "can_use_skill": self._check_skill_availability(player),
            "is_silenced": self._check_silence_effects(player)
        }
        
        return SelfInfo(
            seat=player["seat"],
            alive=player["alive"],
            role=player["role"],
            status=status
        )
    
    def _check_skill_availability(self, player: Dict[str, Any]) -> bool:
        """检查技能是否可用（基于冷却时间和限制）"""
        role = player.get("role", "")
        seat = player.get("seat", 0)
        
        # For roles with limited uses, check event history
        if role == "Witch":
            # Check if witch has already used both potions
            return self._check_witch_potions_available(seat)
        elif role == "Guard":
            # Check if guard can protect (not consecutive nights on same target)
            return self._check_guard_target_available(seat)
        else:
            # Most roles can use skills freely each night
            return True
    
    def _check_silence_effects(self, player: Dict[str, Any]) -> bool:
        """检查是否被沉默"""
        # Currently no silence effects implemented in the game
        # This would check for debuff events affecting the player
        return False
    
    def _check_witch_potions_available(self, seat: int) -> bool:
        """检查女巫是否还有药水可用"""
        # Check event log for witch's previous uses
        from app.database import Event
        
        try:
            poison_used = self.db.query(Event).filter(
                Event.game_id == self.state_machine.current_game_id,
                Event.type == "night_action",
                Event.actor == str(seat),
                Event.payload["action"].astext == "poison"
            ).first() is not None
            
            save_used = self.db.query(Event).filter(
                Event.game_id == self.state_machine.current_game_id,
                Event.type == "night_action",
                Event.actor == str(seat),
                Event.payload["action"].astext == "save"
            ).first() is not None
            
            # Witch can use skills if at least one potion is available
            return not (poison_used and save_used)
        except:
            # If we can't check, assume available
            return True
    
    def _check_guard_target_available(self, seat: int) -> bool:
        """检查守卫是否可以守护（不能连续守护同一目标）"""
        # This is a simplified check - in a full implementation,
        # we'd track the last guarded target from previous night
        try:
            from app.database import Event
            
            # Get the last guard action
            last_guard_action = self.db.query(Event).filter(
                Event.game_id == self.state_machine.current_game_id,
                Event.type == "night_action",
                Event.actor == str(seat),
                Event.payload["action"].astext == "guard"
            ).order_by(Event.timestamp.desc()).first()
            
            if last_guard_action:
                # Check if it was from the immediately previous night
                # For now, just return True to allow guarding
                return True
            
            return True
        except:
            return True
    
    def _get_death_reason(self, seat: int) -> str:
        """获取玩家死亡原因"""
        try:
            from app.database import Event
            
            # Look for death-related events
            death_event = self.db.query(Event).filter(
                Event.game_id == self.state_machine.current_game_id,
                Event.type.in_(["night_result", "vote_result", "hunter_shot"]),
                Event.payload.contains({"killed": seat})
            ).order_by(Event.timestamp.desc()).first()
            
            if death_event:
                if death_event.type == "night_result":
                    return "killed_at_night"
                elif death_event.type == "vote_result":
                    return "voted_out"
                elif death_event.type == "hunter_shot":
                    return "shot_by_hunter"
            
            return "died"
        except:
            return "died"
    
    def _get_last_guarded_target(self, seat: int) -> Optional[int]:
        """获取守卫上一晚守护的目标"""
        try:
            from app.database import Event
            
            last_guard_action = self.db.query(Event).filter(
                Event.game_id == self.state_machine.current_game_id,
                Event.type == "night_action",
                Event.actor == str(seat),
                Event.payload["action"].astext == "guard"
            ).order_by(Event.timestamp.desc()).first()
            
            if last_guard_action and "target_seat" in last_guard_action.payload:
                return last_guard_action.payload["target_seat"]
            
            return None
        except:
            return None
    
    def _get_witch_potion_status(self, seat: int) -> tuple[bool, bool]:
        """获取女巫药水使用状态 (has_save, has_poison)"""
        try:
            from app.database import Event
            
            save_used = self.db.query(Event).filter(
                Event.game_id == self.state_machine.current_game_id,
                Event.type == "night_action",
                Event.actor == str(seat),
                Event.payload["action"].astext == "save"
            ).first() is not None
            
            poison_used = self.db.query(Event).filter(
                Event.game_id == self.state_machine.current_game_id,
                Event.type == "night_action",
                Event.actor == str(seat),
                Event.payload["action"].astext == "poison"
            ).first() is not None
            
            return (not save_used, not poison_used)
        except:
            return (True, True)  # Default to having both potions
    
    def _build_public_state(self, game_state) -> PublicState:
        """构建公开状态信息"""
        
        # Get revealed identities (dead players)
        revealed_identities = []
        for seat in game_state.dead_players:
            player = game_state.players.get(seat)
            if player:
                revealed_identities.append({
                    "seat": seat,
                    "role": player["role"],
                    "reason": self._get_death_reason(seat)
                })
        
        # Get last night result (public information only)
        last_night_result = {
            "killed": [s for s in game_state.dead_players if s in game_state.dead_players]  # Simplified
        }
        
        return PublicState(
            player_count=len(game_state.players),
            alive_seats=game_state.get_alive_players(),
            revealed_identities=revealed_identities,
            last_night_result=last_night_result
        )
    
    def _build_chat_history(
        self, 
        game_id: str, 
        seat: int, 
        player: Dict[str, Any]
    ) -> ChatHistory:
        """构建聊天历史 - 基于可见性约束"""
        
        # Get recent events
        events = self.db.query(Event).filter(
            Event.game_id == game_id,
            Event.type == "Speak"
        ).order_by(Event.idx.desc()).limit(50).all()
        
        public_chat = []
        team_chat = []
        
        for event in reversed(events):  # Restore chronological order
            payload = event.payload
            event_visibility = payload.get("visibility", "public")
            speaker_seat = payload.get("seat")
            content = payload.get("content", "")
            
            message = ChatMessage(
                idx=event.idx,
                seat=speaker_seat,
                text=content
            )
            
            if event_visibility == "public":
                public_chat.append(message)
            elif event_visibility == "team":
                # Only show team chat if player is in same team
                if self._can_see_team_chat(player, speaker_seat):
                    team_chat.append(message)
        
        return ChatHistory(
            public_chat_tail=public_chat[-20:],  # Last 20 messages
            team_chat_tail=team_chat[-10:]       # Last 10 team messages
        )
    
    def _build_private_notes(self, game_id: str, seat: int) -> List[PrivateNote]:
        """构建私密通知"""
        
        # Get system notices targeted at this player
        events = self.db.query(Event).filter(
            Event.game_id == game_id,
            Event.type.in_(["SystemNotice", "NightResult"])
        ).order_by(Event.idx).all()
        
        private_notes = []
        
        for event in events:
            payload = event.payload
            
            if event.type == "SystemNotice":
                target_seats = payload.get("target_seats")
                if target_seats is None or seat in target_seats:
                    private_notes.append(PrivateNote(
                        idx=event.idx,
                        content=payload.get("message", "")
                    ))
            
            elif event.type == "NightResult":
                # Extract relevant info for this player
                results = payload.get("results", {})
                inspected = results.get("inspected", {})
                
                if seat in inspected:
                    target_seat = seat
                    alignment = inspected[seat]
                    private_notes.append(PrivateNote(
                        idx=event.idx,
                        content=f"你查验了{target_seat}号玩家，结果：{alignment}阵营"
                    ))
                
                # If player was saved by witch
                if seat in results.get("saved", []):
                    private_notes.append(PrivateNote(
                        idx=event.idx,
                        content="你被女巫救了！"
                    ))
        
        return private_notes
    
    def _can_see_team_chat(self, player: Dict[str, Any], speaker_seat: int) -> bool:
        """检查是否可以看到队内聊天"""
        
        player_alignment = player.get("alignment")
        if player_alignment != "Werewolf":
            return False
        
        # Get speaker's alignment from game state
        game_state = self.state_machine.get_game(player["game_id"]) 
        if not game_state:
            return False
        
        speaker = game_state.players.get(speaker_seat)
        if not speaker:
            return False
        
        return speaker.get("alignment") == "Werewolf"
    
    def get_allowed_actions(self, game_id: str, seat: int) -> List[str]:
        """获取允许的行动列表"""
        
        game_state = self.state_machine.get_game(game_id)
        if not game_state:
            return []
        
        player = game_state.players.get(seat)
        if not player or not player.get("alive", True):
            return []
        
        current_phase = game_state.current_phase
        role = player.get("role")
        
        allowed = []
        
        # Speaking is always allowed (context routing handled by service)
        allowed.append("say")
        
        # Phase-specific actions
        if current_phase.value == "Vote":
            allowed.append("vote")
        
        elif current_phase.value == "Night":
            # Role-specific night actions
            if role == "Werewolf":
                allowed.append("night_action_kill")
            elif role == "Seer":
                allowed.append("night_action_inspect")
            elif role == "Witch":
                allowed.extend(["night_action_save", "night_action_poison"])
            elif role == "Guard":
                allowed.append("night_action_guard")
        
        # Always allow asking GM for clarification
        allowed.append("ask_gm_for_clarification")
        
        return allowed
    
    def get_action_constraints(self, game_id: str, seat: int) -> Dict[str, Any]:
        """获取行动约束"""
        
        game_state = self.state_machine.get_game(game_id)
        if not game_state:
            return {}
        
        player = game_state.players.get(seat)
        if not player:
            return {}
        
        constraints = {}
        
        # Voting constraints
        if "vote" in self.get_allowed_actions(game_id, seat):
            constraints["vote_targets"] = game_state.get_alive_players()
        
        # Night action constraints
        role = player.get("role")
        if role == "Werewolf":
            # Can't kill other werewolves
            werewolf_seats = game_state.get_players_by_role("Werewolf")
            valid_targets = [s for s in game_state.get_alive_players() if s not in werewolf_seats]
            constraints["kill_targets"] = valid_targets
        
        elif role == "Seer":
            # Can inspect anyone except self
            constraints["inspect_targets"] = [s for s in game_state.get_alive_players() if s != seat]
        
        elif role == "Guard":
            # Can guard anyone except self, and not same person twice in a row
            valid_targets = [s for s in game_state.get_alive_players() if s != seat]
            last_guarded = self._get_last_guarded_target(seat)
            if last_guarded:
                valid_targets = [s for s in valid_targets if s != last_guarded]
            constraints["guard_targets"] = valid_targets
        
        elif role == "Witch":
            # Track witch's potion usage - they can only use each potion once per game
            has_save, has_poison = self._get_witch_potion_status(seat)
            if has_save:
                constraints["save_targets"] = game_state.get_alive_players()
            if has_poison:
                constraints["poison_targets"] = game_state.get_alive_players()
        
        return constraints