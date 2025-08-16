"""Admin routes for LLM provider management - implements D01 specification"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.database import get_db, Provider, Preset, Binding
from app.routers.auth import get_current_user, User

router = APIRouter()

# Request/Response models
class ProviderRequest(BaseModel):
    name: str
    type: str
    base_url: str
    api_key: str
    default_model: str
    headers: Optional[Dict[str, str]] = {}
    timeout_s: Optional[int] = 60
    rate_limit_tpm: Optional[int] = None
    rate_limit_rpm: Optional[int] = None
    enabled: Optional[bool] = True

class ProviderResponse(BaseModel):
    id: str
    name: str
    type: str
    base_url: str
    default_model: str
    headers: Dict[str, str]
    timeout_s: int
    rate_limit_tpm: Optional[int]
    rate_limit_rpm: Optional[int]
    enabled: bool
    created_at: datetime

class PresetRequest(BaseModel):
    provider_id: str
    model_id: str
    name: str
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = 2048
    seed: Optional[int] = None
    stop: Optional[List[str]] = None
    modalities: Optional[List[str]] = ["text"]
    tools_allowed: Optional[bool] = True
    vision_max_pixels: Optional[int] = None

class PresetResponse(BaseModel):
    id: str
    provider_id: str
    model_id: str
    name: str
    temperature: float
    top_p: float
    max_tokens: int
    seed: Optional[int]
    stop: Optional[List[str]]
    modalities: List[str]
    tools_allowed: bool
    vision_max_pixels: Optional[int]
    created_at: datetime

class BindingRequest(BaseModel):
    scope: str  # global/room/seat/agent_role
    scope_key: str
    preset_id: str
    priority: Optional[int] = 0

class BindingResponse(BaseModel):
    id: str
    scope: str
    scope_key: str
    preset_id: str
    priority: int
    created_at: datetime

class ModelResolutionResponse(BaseModel):
    provider: Dict[str, Any]
    model_configuration: Dict[str, Any]
    resolution_trace: List[Dict[str, Any]]

# TODO: Implement proper admin authentication
def get_admin_user(current_user: User = Depends(get_current_user)):
    """Verify admin permissions"""
    # For now, allow all authenticated users
    # In production, check admin role/permissions
    return current_user

# Provider Management
@router.post("/providers", response_model=ProviderResponse)
async def create_provider(
    request: ProviderRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Create a new LLM provider"""
    
    provider = Provider(
        id=f"prov-{uuid.uuid4().hex[:8]}",
        name=request.name,
        type=request.type,
        base_url=request.base_url,
        api_key=request.api_key,  # TODO: Encrypt this
        default_model=request.default_model,
        headers=request.headers or {},
        timeout_s=request.timeout_s,
        rate_limit_tpm=request.rate_limit_tpm,
        rate_limit_rpm=request.rate_limit_rpm,
        enabled=request.enabled
    )
    
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        type=provider.type,
        base_url=provider.base_url,
        default_model=provider.default_model,
        headers=provider.headers,
        timeout_s=provider.timeout_s,
        rate_limit_tpm=provider.rate_limit_tpm,
        rate_limit_rpm=provider.rate_limit_rpm,
        enabled=provider.enabled,
        created_at=provider.created_at
    )

@router.get("/providers", response_model=List[ProviderResponse])
async def list_providers(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """List all providers (with API keys masked)"""
    
    providers = db.query(Provider).all()
    
    return [ProviderResponse(
        id=p.id,
        name=p.name,
        type=p.type,
        base_url=p.base_url,
        default_model=p.default_model,
        headers=p.headers,
        timeout_s=p.timeout_s,
        rate_limit_tpm=p.rate_limit_tpm,
        rate_limit_rpm=p.rate_limit_rpm,
        enabled=p.enabled,
        created_at=p.created_at
    ) for p in providers]

@router.patch("/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    request: ProviderRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Update provider configuration"""
    
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    # Update fields
    provider.name = request.name
    provider.type = request.type
    provider.base_url = request.base_url
    provider.api_key = request.api_key  # TODO: Only update if provided
    provider.default_model = request.default_model
    provider.headers = request.headers or {}
    provider.timeout_s = request.timeout_s
    provider.rate_limit_tpm = request.rate_limit_tpm
    provider.rate_limit_rpm = request.rate_limit_rpm
    provider.enabled = request.enabled
    
    db.commit()
    
    return {"message": "Provider updated successfully"}

@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Delete a provider"""
    
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    db.delete(provider)
    db.commit()
    
    return {"message": "Provider deleted successfully"}

# Preset Management
@router.post("/presets", response_model=PresetResponse)
async def create_preset(
    request: PresetRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Create a new model preset"""
    
    # Verify provider exists
    provider = db.query(Provider).filter(Provider.id == request.provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    preset = Preset(
        id=f"preset-{uuid.uuid4().hex[:8]}",
        provider_id=request.provider_id,
        model_id=request.model_id,
        name=request.name,
        temperature=int(request.temperature * 100),  # Store as int * 100
        top_p=int(request.top_p * 100),
        max_tokens=request.max_tokens,
        seed=request.seed,
        stop=request.stop,
        modalities=request.modalities,
        tools_allowed=request.tools_allowed,
        vision_max_pixels=request.vision_max_pixels
    )
    
    db.add(preset)
    db.commit()
    db.refresh(preset)
    
    return PresetResponse(
        id=preset.id,
        provider_id=preset.provider_id,
        model_id=preset.model_id,
        name=preset.name,
        temperature=preset.temperature / 100.0,
        top_p=preset.top_p / 100.0,
        max_tokens=preset.max_tokens,
        seed=preset.seed,
        stop=preset.stop,
        modalities=preset.modalities,
        tools_allowed=preset.tools_allowed,
        vision_max_pixels=preset.vision_max_pixels,
        created_at=preset.created_at
    )

@router.get("/presets", response_model=List[PresetResponse])
async def list_presets(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """List all presets"""
    
    presets = db.query(Preset).all()
    
    return [PresetResponse(
        id=p.id,
        provider_id=p.provider_id,
        model_id=p.model_id,
        name=p.name,
        temperature=p.temperature / 100.0,
        top_p=p.top_p / 100.0,
        max_tokens=p.max_tokens,
        seed=p.seed,
        stop=p.stop,
        modalities=p.modalities,
        tools_allowed=p.tools_allowed,
        vision_max_pixels=p.vision_max_pixels,
        created_at=p.created_at
    ) for p in presets]

# Binding Management
@router.post("/bindings", response_model=BindingResponse)
async def create_binding(
    request: BindingRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Create a new preset binding"""
    
    # Verify preset exists
    preset = db.query(Preset).filter(Preset.id == request.preset_id).first()
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preset not found"
        )
    
    binding = Binding(
        id=f"bind-{uuid.uuid4().hex[:8]}",
        scope=request.scope,
        scope_key=request.scope_key,
        preset_id=request.preset_id,
        priority=request.priority
    )
    
    db.add(binding)
    db.commit()
    db.refresh(binding)
    
    return BindingResponse(
        id=binding.id,
        scope=binding.scope,
        scope_key=binding.scope_key,
        preset_id=binding.preset_id,
        priority=binding.priority,
        created_at=binding.created_at
    )

@router.get("/bindings", response_model=List[BindingResponse])
async def list_bindings(
    scope: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """List bindings, optionally filtered by scope"""
    
    query = db.query(Binding)
    if scope:
        query = query.filter(Binding.scope == scope)
    
    bindings = query.all()
    
    return [BindingResponse(
        id=b.id,
        scope=b.scope,
        scope_key=b.scope_key,
        preset_id=b.preset_id,
        priority=b.priority,
        created_at=b.created_at
    ) for b in bindings]

@router.delete("/bindings/{binding_id}")
async def delete_binding(
    binding_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Delete a binding"""
    
    binding = db.query(Binding).filter(Binding.id == binding_id).first()
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Binding not found"
        )
    
    db.delete(binding)
    db.commit()
    
    return {"message": "Binding deleted successfully"}

# Model Resolution API
@router.get("/resolve-model", response_model=ModelResolutionResponse)
async def resolve_model(
    room_id: Optional[str] = Query(None),
    seat: Optional[int] = Query(None),
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Resolve model configuration based on context"""
    
    # Get all applicable bindings ordered by priority
    bindings = db.query(Binding).order_by(Binding.priority.desc()).all()
    
    resolution_trace = []
    selected_preset = None
    
    # Apply bindings in priority order
    for binding in bindings:
        match = False
        
        if binding.scope == "global":
            match = True
        elif binding.scope == "room" and room_id == binding.scope_key:
            match = True
        elif binding.scope == "seat" and seat is not None and str(seat) == binding.scope_key:
            match = True
        elif binding.scope == "agent_role" and role == binding.scope_key:
            match = True
        
        if match:
            resolution_trace.append({
                "scope": binding.scope,
                "scope_key": binding.scope_key,
                "preset_id": binding.preset_id,
                "priority": binding.priority
            })
            
            if selected_preset is None:  # Use highest priority match
                selected_preset = db.query(Preset).filter(
                    Preset.id == binding.preset_id
                ).first()
    
    if not selected_preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No applicable model configuration found"
        )
    
    # Get provider info
    provider = db.query(Provider).filter(
        Provider.id == selected_preset.provider_id
    ).first()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Provider not found for preset"
        )
    
    return ModelResolutionResponse(
        provider={
            "id": provider.id,
            "type": provider.type,
            "base_url": provider.base_url
        },
        model_configuration={
            "model_id": selected_preset.model_id,
            "temperature": selected_preset.temperature / 100.0,
            "top_p": selected_preset.top_p / 100.0,
            "max_tokens": selected_preset.max_tokens,
            "tools_allowed": selected_preset.tools_allowed
        },
        resolution_trace=resolution_trace
    )