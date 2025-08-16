"""Agent configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class AgentSettings(BaseSettings):
    """Agent settings"""
    
    # API Configuration
    api_base_url: str = "http://localhost:8000"
    
    # LLM Provider Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Agent Behavior
    default_temperature: float = 0.7
    max_tokens: int = 2048
    
    # Development
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = AgentSettings()