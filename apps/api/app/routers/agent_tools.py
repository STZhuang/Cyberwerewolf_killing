"""Agent-specific tool endpoints for D03 specification"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
import logging

from app.database import get_db
from app.agent.tools_service import AgentToolsService
from app.game.game_service import GameService
from app.main import manager

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentSpeakRequest(BaseModel):
    game_id: str
    seat: int
    text: str


class AgentVoteRequest(BaseModel):
    game_id: str
    seat: int
    target_seat: Optional[int] = None


class AgentNightActionRequest(BaseModel):
    game_id: str
    seat: int
    action: Literal["kill", "save", "poison", "inspect", "guard"]
    target_seat: Optional[int] = None


class AgentGMQuestionRequest(BaseModel):
    game_id: str
    seat: int
    question: str


@router.post("/agent/say")
async def agent_say(
    request: AgentSpeakRequest,
    db: Session = Depends(get_db)
):
    """Agent speak tool endpoint"""
    if not manager.game_service:
        raise HTTPException(status_code=503, detail="Game service unavailable")
    
    tools_service = AgentToolsService(db, manager.game_service)
    result = await tools_service.say(request.game_id, request.seat, request.text)
    
    return result.dict()


@router.post("/agent/vote")
async def agent_vote(
    request: AgentVoteRequest,
    db: Session = Depends(get_db)
):
    """Agent vote tool endpoint"""
    if not manager.game_service:
        raise HTTPException(status_code=503, detail="Game service unavailable")
    
    tools_service = AgentToolsService(db, manager.game_service)
    result = await tools_service.vote(request.game_id, request.seat, request.target_seat)
    
    return result.dict()


@router.post("/agent/night-action")
async def agent_night_action(
    request: AgentNightActionRequest,
    db: Session = Depends(get_db)
):
    """Agent night action tool endpoint"""
    if not manager.game_service:
        raise HTTPException(status_code=503, detail="Game service unavailable")
    
    tools_service = AgentToolsService(db, manager.game_service)
    result = await tools_service.night_action(
        request.game_id, 
        request.seat, 
        request.action, 
        request.target_seat
    )
    
    return result.dict()


@router.post("/agent/ask-gm")
async def agent_ask_gm(
    request: AgentGMQuestionRequest,
    db: Session = Depends(get_db)
):
    """Agent GM question tool endpoint"""
    if not manager.game_service:
        raise HTTPException(status_code=503, detail="Game service unavailable")
    
    tools_service = AgentToolsService(db, manager.game_service)
    result = await tools_service.ask_gm_for_clarification(
        request.game_id, 
        request.seat, 
        request.question
    )
    
    return result.dict()