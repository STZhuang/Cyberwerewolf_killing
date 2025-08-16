"""Game service - integrates state machine, event sourcing, and WebSocket broadcasting"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import asyncio

from app.game.state_machine import GameStateMachine, GamePhase
from app.game.event_sourcing import *
from app.database import Game, GamePlayer, RoomMember, Room
from app.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

class GameService:
    """游戏服务 - 统一管理游戏逻辑、事件和WebSocket通信"""
    
    def __init__(self, db: Session, ws_manager: ConnectionManager):
        self.db = db
        self.ws_manager = ws_manager
        self.state_machine = GameStateMachine()
        self.event_manager = GameEventManager(db)
        
        # Subscribe to events for WebSocket broadcasting
        self.event_manager.publisher.subscribe(self._on_event)
    
    async def _on_event(self, event: BaseEvent):
        """事件处理器 - 将事件广播到WebSocket"""
        try:
            # Find room_id for the game
            game_record = self.db.query(Game).filter(Game.id == event.game_id).first()
            if not game_record:
                return
            
            room_id = game_record.room_id
            
            # Convert event to WebSocket message format
            ws_message = {
                "type": self._event_to_ws_type(event.get_event_type()),
                "payload": event.to_payload(),
                "timestamp": int(event.timestamp.timestamp() * 1000)
            }
            
            # Determine visibility and target seats
            visibility = self._get_event_visibility(event)
            target_seats = self._get_event_target_seats(event)
            
            # Broadcast message
            await self.ws_manager.broadcast_to_room(
                room_id, 
                ws_message, 
                target_seats=target_seats
            )
            
        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
    
    def _event_to_ws_type(self, event_type: str) -> str:
        """将事件类型转换为WebSocket消息类型"""
        mapping = {
            "Speak": "speak",
            "Vote": "vote", 
            "VoteResult": "system",
            "NightAction": "night_action",
            "NightResult": "system",
            "PhaseChanged": "state",
            "SystemNotice": "system",
            "GameEnded": "system"
        }
        return mapping.get(event_type, "system")
    
    def _get_event_visibility(self, event: BaseEvent) -> str:
        """获取事件可见性"""
        if isinstance(event, (SpeakEvent, VoteEvent)):
            return getattr(event, 'visibility', 'public')
        elif isinstance(event, NightActionEvent):
            return 'team'  # Only visible to team members
        else:
            return 'public'
    
    def _get_event_target_seats(self, event: BaseEvent) -> Optional[List[int]]:
        """获取事件目标座位"""
        if isinstance(event, SystemNoticeEvent):
            return event.target_seats
        elif isinstance(event, NightActionEvent):
            # Only visible to werewolves during night
            game_state = self.state_machine.get_game(event.game_id)
            if game_state:
                return game_state.get_players_by_alignment("Werewolf")
        return None
    
    async def create_game(self, room_id: str, config: Dict[str, Any]) -> str:
        """创建游戏"""
        
        # Get room and members
        room = self.db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise ValueError("Room not found")
        
        members = self.db.query(RoomMember).filter(
            RoomMember.room_id == room_id,
            RoomMember.left_at.is_(None)
        ).all()
        
        # Create game record
        import uuid
        game_id = str(uuid.uuid4())
        
        game_record = Game(
            id=game_id,
            room_id=room_id,
            seed=str(uuid.uuid4()),
            config=config,
            current_phase=GamePhase.LOBBY.value,
            current_round=0
        )
        
        self.db.add(game_record)
        self.db.commit()
        
        # Create game state
        game_state = self.state_machine.create_game(game_id, config)
        
        # Emit game created event
        players_data = [{
            "user_id": member.user_id,
            "seat": member.seat,
            "is_bot": member.is_bot,
            "agent_id": member.agent_id
        } for member in members]
        
        event = GameCreatedEvent(
            game_id=game_id,
            timestamp=datetime.utcnow(),
            actor="system",
            config=config,
            players=players_data
        )
        
        self.event_manager.emit(event)
        
        logger.info(f"Created game {game_id} for room {room_id}")
        return game_id
    
    async def start_game(self, game_id: str) -> Dict[str, Any]:
        """开始游戏 - 分配角色"""
        
        game_record = self.db.query(Game).filter(Game.id == game_id).first()
        if not game_record:
            raise ValueError("Game not found")
        
        # Get members
        members = self.db.query(RoomMember).filter(
            RoomMember.room_id == game_record.room_id,
            RoomMember.left_at.is_(None)
        ).all()
        
        players_data = [{
            "user_id": member.user_id,
            "seat": member.seat,
            "is_bot": member.is_bot,
            "agent_id": member.agent_id
        } for member in members]
        
        # Assign roles
        role_assignments = self.state_machine.assign_roles(game_id, players_data)
        
        # Create GamePlayer records
        for assignment in role_assignments:
            game_player = GamePlayer(
                game_id=game_id,
                user_id=next(p["user_id"] for p in players_data if p["seat"] == assignment["seat"]),
                seat=assignment["seat"],
                role=assignment["role"],
                alignment=assignment["alignment"],
                alive=True,
                is_bot=next(p["is_bot"] for p in players_data if p["seat"] == assignment["seat"]),
                agent_id=next((p["agent_id"] for p in players_data if p["seat"] == assignment["seat"]), None)
            )
            self.db.add(game_player)
        
        # Update game record
        game_record.current_phase = GamePhase.NIGHT.value
        game_record.current_round = 1
        game_record.started_at = datetime.utcnow()
        
        self.db.commit()
        
        # Emit events
        roles_event = RolesAssignedEvent(
            game_id=game_id,
            timestamp=datetime.utcnow(),
            actor="system",
            assignments=role_assignments,
            seed=game_record.seed
        )
        
        self.event_manager.emit(roles_event)
        
        # Start first night phase
        await self._start_phase(game_id, GamePhase.NIGHT)
        
        return {"message": "Game started", "assignments": role_assignments}
    
    async def _start_phase(self, game_id: str, phase: GamePhase):
        """开始新阶段"""
        
        phase_data = self.state_machine.start_phase(game_id, phase)
        
        # Update game record
        game_record = self.db.query(Game).filter(Game.id == game_id).first()
        if game_record:
            game_record.current_phase = phase.value
            game_record.current_round = phase_data["round"]
            self.db.commit()
        
        # Emit phase change event
        event = PhaseChangedEvent(
            game_id=game_id,
            timestamp=datetime.utcnow(),
            actor="system",
            from_phase=game_record.current_phase if game_record else "unknown",
            to_phase=phase.value,
            round_number=phase_data["round"],
            deadline=phase_data.get("deadline")
        )
        
        self.event_manager.emit(event)
        
        # Schedule phase timeout
        if phase_data.get("deadline"):
            asyncio.create_task(self._schedule_phase_timeout(game_id, phase))
    
    async def _schedule_phase_timeout(self, game_id: str, phase: GamePhase):
        """调度阶段超时"""
        game_state = self.state_machine.get_game(game_id)
        if not game_state or not game_state.phase_deadline:
            return
        
        # Wait until deadline
        now = datetime.utcnow()
        if game_state.phase_deadline > now:
            wait_seconds = (game_state.phase_deadline - now).total_seconds()
            await asyncio.sleep(wait_seconds)
        
        # Check if phase is still active
        current_game_state = self.state_machine.get_game(game_id)
        if not current_game_state or current_game_state.current_phase != phase:
            return
        
        # Emit timer ended event
        event = TimerEndedEvent(
            game_id=game_id,
            timestamp=datetime.utcnow(),
            actor="system",
            phase=phase.value
        )
        
        self.event_manager.emit(event)
        
        # Auto-advance phase
        await self.advance_phase(game_id)
    
    async def submit_speak(self, game_id: str, seat: int, content: str) -> Dict[str, Any]:
        """提交发言"""
        
        game_state = self.state_machine.get_game(game_id)
        if not game_state:
            raise ValueError("Game not found")
        
        if seat not in game_state.get_alive_players():
            raise ValueError("Player is not alive")
        
        # Phase validation: allow DayTalk publicly; allow Night for werewolves team chat
        if game_state.current_phase not in (GamePhase.DAY_TALK, GamePhase.NIGHT):
            raise ValueError("Not in talk phase")

        # Determine visibility based on phase and role
        visibility = "public"
        if game_state.current_phase == GamePhase.NIGHT:
            player = game_state.players.get(seat)
            if player and player["role"] == "Werewolf":
                visibility = "team"
            else:
                # Non-werewolves cannot speak at night
                raise ValueError("Speaking not allowed at night for this role")
        
        # Emit speak event
        event = SpeakEvent(
            game_id=game_id,
            timestamp=datetime.utcnow(),
            actor=str(seat),
            seat=seat,
            content=content,
            phase=game_state.current_phase.value,
            visibility=visibility
        )
        
        self.event_manager.emit(event)
        
        return {"success": True, "visibility": visibility}
    
    async def submit_vote(self, game_id: str, seat: int, target_seat: Optional[int]) -> Dict[str, Any]:
        """提交投票"""
        
        vote_data = self.state_machine.submit_vote(game_id, seat, target_seat)
        
        # Emit vote event
        event = VoteEvent(
            game_id=game_id,
            timestamp=datetime.utcnow(),
            actor=str(seat),
            seat=seat,
            target_seat=target_seat,
            phase=GamePhase.VOTE.value
        )
        
        self.event_manager.emit(event)
        
        return vote_data
    
    async def submit_night_action(
        self, 
        game_id: str, 
        seat: int, 
        action: str, 
        target_seat: Optional[int] = None
    ) -> Dict[str, Any]:
        """提交夜间行动"""
        
        game_state = self.state_machine.get_game(game_id)
        if not game_state:
            raise ValueError("Game not found")
        
        player = game_state.players.get(seat)
        if not player:
            raise ValueError("Player not found")
        
        action_data = self.state_machine.submit_night_action(game_id, seat, action, target_seat)
        
        # Emit night action event
        event = NightActionEvent(
            game_id=game_id,
            timestamp=datetime.utcnow(),
            actor=str(seat),
            seat=seat,
            action=action,
            target_seat=target_seat,
            role=player["role"]
        )
        
        self.event_manager.emit(event)
        
        return action_data
    
    async def advance_phase(self, game_id: str) -> Optional[Dict[str, Any]]:
        """推进阶段"""
        
        game_state = self.state_machine.get_game(game_id)
        if not game_state:
            raise ValueError("Game not found")
        
        current_phase = game_state.current_phase
        
        # Handle phase-specific logic before advancing
        if current_phase == GamePhase.VOTE:
            # Resolve voting
            vote_result = self.state_machine.resolve_vote(game_id)
            
            # Emit vote result event
            event = VoteResultEvent(
                game_id=game_id,
                timestamp=datetime.utcnow(),
                actor="system",
                votes=dict(game_state.votes),
                executed_seat=vote_result.get("executed_seat"),
                reason=vote_result.get("reason", "unknown")
            )
            
            self.event_manager.emit(event)
            
            # Emit player death event if someone was executed
            if vote_result.get("executed_seat"):
                death_event = PlayerDiedEvent(
                    game_id=game_id,
                    timestamp=datetime.utcnow(),
                    actor="system",
                    seat=vote_result["executed_seat"],
                    cause="voted"
                )
                self.event_manager.emit(death_event)
        
        elif current_phase == GamePhase.NIGHT:
            # Resolve night actions
            night_result = self.state_machine.resolve_night(game_id)
            
            # Emit night result event
            event = NightResultEvent(
                game_id=game_id,
                timestamp=datetime.utcnow(),
                actor="system",
                results=night_result
            )
            
            self.event_manager.emit(event)
            
            # Emit player death events
            for seat in night_result.get("killed", []):
                death_event = PlayerDiedEvent(
                    game_id=game_id,
                    timestamp=datetime.utcnow(),
                    actor="system",
                    seat=seat,
                    cause="killed"
                )
                self.event_manager.emit(death_event)
            
            for seat in night_result.get("poisoned", []):
                death_event = PlayerDiedEvent(
                    game_id=game_id,
                    timestamp=datetime.utcnow(),
                    actor="system",
                    seat=seat,
                    cause="poisoned"
                )
                self.event_manager.emit(death_event)
        
        # Advance to next phase
        next_phase_data = self.state_machine.advance_to_next_phase(game_id)
        
        if next_phase_data:
            # Update game record
            game_record = self.db.query(Game).filter(Game.id == game_id).first()
            if game_record:
                game_record.current_phase = game_state.current_phase.value
                game_record.current_round = game_state.current_round
                
                if game_state.current_phase == GamePhase.END:
                    game_record.ended_at = datetime.utcnow()
                
                self.db.commit()
            
            # Emit phase change event
            phase_event = PhaseChangedEvent(
                game_id=game_id,
                timestamp=datetime.utcnow(),
                actor="system",
                from_phase=current_phase.value,
                to_phase=game_state.current_phase.value,
                round_number=game_state.current_round,
                deadline=next_phase_data.get("deadline")
            )
            
            self.event_manager.emit(phase_event)
            
            # Check if game ended
            if game_state.current_phase == GamePhase.END:
                end_event = GameEndedEvent(
                    game_id=game_id,
                    timestamp=datetime.utcnow(),
                    actor="system",
                    winner=game_state.winner or "unknown",
                    final_state={
                        "players": dict(game_state.players),
                        "rounds": game_state.current_round
                    }
                )
                
                self.event_manager.emit(end_event)
            else:
                # Schedule next phase timeout
                if next_phase_data.get("deadline"):
                    asyncio.create_task(self._schedule_phase_timeout(game_id, game_state.current_phase))
        
        return next_phase_data
    
    def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        """获取游戏状态"""
        
        game_state = self.state_machine.get_game(game_id)
        if not game_state:
            return None
        
        return {
            "game_id": game_id,
            "phase": game_state.current_phase.value,
            "round": game_state.current_round,
            "players": [
                {
                    "seat": seat,
                    "alive": player["alive"],
                    "role": player["role"] if not player["alive"] else None  # Only show role if dead
                }
                for seat, player in game_state.players.items()
            ],
            "deadline": int(game_state.phase_deadline.timestamp() * 1000) if game_state.phase_deadline else None
        }
