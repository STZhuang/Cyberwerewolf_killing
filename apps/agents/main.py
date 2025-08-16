"""Agent service main entry point"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn

from config import settings
from agent_manager import agent_manager

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# FastAPI app for agent service
app = FastAPI(
    title="Cyber Werewolves Agent Service",
    description="LLM agents for werewolf game players",
    version="0.1.0"
)

# Request/Response models
class CreateAgentRequest(BaseModel):
    agent_id: str
    role: str
    model_provider: str = "openai"
    custom_llm_config: Optional[Dict[str, Any]] = None

class AgentDecisionRequest(BaseModel):
    game_id: str
    seat: int
    context: Dict[str, Any]
    prompt: Optional[str] = ""

class GMQuestionRequest(BaseModel):
    game_id: str
    question: str

class RegisterGameAgentRequest(BaseModel):
    game_id: str
    seat: int
    agent_id: str

@app.get("/")
async def root():
    """Health check"""
    return {"message": "Agent service is running"}

@app.post("/agents")
async def create_agent(request: CreateAgentRequest):
    """Create a new agent for a role"""
    
    try:
        agent = agent_manager.create_agent_for_role(
            request.agent_id,
            request.role,
            request.model_provider,
            request.custom_llm_config
        )
        
        if not agent:
            raise HTTPException(status_code=400, detail="Failed to create agent")
        
        return {
            "message": "Agent created successfully",
            "agent_id": request.agent_id,
            "role": request.role
        }
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/gm")
async def create_gm_agent(game_id: str, model_provider: str = "openai"):
    """Create GM agent for a game"""
    
    try:
        agent = agent_manager.create_gm_agent(game_id, model_provider)
        
        if not agent:
            raise HTTPException(status_code=400, detail="Failed to create GM agent")
        
        return {
            "message": "GM agent created successfully",
            "game_id": game_id
        }
        
    except Exception as e:
        logger.error(f"Error creating GM agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/register")
async def register_game_agent(request: RegisterGameAgentRequest):
    """Register an agent for a game seat"""
    
    try:
        agent_manager.register_game_agent(
            request.game_id,
            request.seat,
            request.agent_id
        )
        
        return {
            "message": "Agent registered successfully",
            "game_id": request.game_id,
            "seat": request.seat,
            "agent_id": request.agent_id
        }
        
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/decision")
async def process_agent_decision(request: AgentDecisionRequest):
    """Process an agent decision"""
    
    try:
        result = await agent_manager.process_agent_decision(
            request.game_id,
            request.seat,
            request.context,
            request.prompt or ""
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing agent decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gm/ask")
async def ask_gm(request: GMQuestionRequest):
    """Ask GM a question"""
    
    try:
        response = await agent_manager.ask_gm(request.game_id, request.question)
        
        return {
            "question": request.question,
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Error asking GM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/games/{game_id}/agents")
async def cleanup_game_agents(game_id: str):
    """Cleanup agents when game ends"""
    
    try:
        agent_manager.cleanup_game_agents(game_id)
        
        return {"message": f"Cleaned up agents for game {game_id}"}
        
    except Exception as e:
        logger.error(f"Error cleaning up agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/status")
async def get_agent_status():
    """Get current agent status"""
    
    return {
        "total_agents": len(agent_manager.agents),
        "active_games": len(agent_manager.game_agents),
        "gm_agents": len(agent_manager.gm_agents)
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug
    )