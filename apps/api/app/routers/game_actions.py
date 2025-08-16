"""Game action routes to back tool APIs (D03)"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
import logging

from app.database import get_db, Game, GamePlayer
from app.routers.auth import get_current_user
from app.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()


class SpeakRequest(BaseModel):
    content: str


class VoteRequest(BaseModel):
    target_seat: Optional[int] = None


class NightActionRequest(BaseModel):
    action: Literal["kill", "save", "poison", "inspect", "guard"]
    target_seat: Optional[int] = None


def _get_player_seat(db: Session, game_id: str, user_id: str) -> int:
    """Resolve player's seat in a game by user_id."""
    gp = db.query(GamePlayer).filter(
        GamePlayer.game_id == game_id,
        GamePlayer.user_id == user_id,
    ).first()
    if not gp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found in this game",
        )
    return gp.seat


@router.post("/games/{game_id}/speak")
async def speak(
    game_id: str,
    request: SpeakRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a speak action for the authenticated player."""
    if not manager.game_service:
        raise HTTPException(status_code=503, detail="Game service unavailable")

    # Ensure game exists
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    seat = _get_player_seat(db, game_id, current_user.id)

    try:
        result = await manager.game_service.submit_speak(game_id, seat, request.content)
        return {"ok": True, "data": result}
    except ValueError as e:
        return {"ok": False, "error": {"code": "INVALID_ACTION", "message": str(e)}}


@router.post("/games/{game_id}/vote")
async def vote(
    game_id: str,
    request: VoteRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a vote for the authenticated player."""
    if not manager.game_service:
        raise HTTPException(status_code=503, detail="Game service unavailable")

    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    seat = _get_player_seat(db, game_id, current_user.id)

    try:
        result = await manager.game_service.submit_vote(game_id, seat, request.target_seat)
        return {"ok": True, "data": result}
    except ValueError as e:
        # Attempt to classify common errors
        msg = str(e)
        code = "INVALID_PHASE" if "Not in voting phase" in msg else "INVALID_ACTION"
        return {"ok": False, "error": {"code": code, "message": msg}}


@router.post("/games/{game_id}/night-action")
async def night_action(
    game_id: str,
    request: NightActionRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a night action for the authenticated player."""
    if not manager.game_service:
        raise HTTPException(status_code=503, detail="Game service unavailable")

    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    seat = _get_player_seat(db, game_id, current_user.id)

    try:
        result = await manager.game_service.submit_night_action(
            game_id, seat, request.action, request.target_seat
        )
        return {"ok": True, "data": result}
    except ValueError as e:
        msg = str(e)
        code = "INVALID_PHASE" if "Not in night phase" in msg else "INVALID_ACTION"
        return {"ok": False, "error": {"code": code, "message": msg}}

