"""LLM Configuration management API (D01 specification)"""

# Configure Python path for SDK imports
from app.path_config import *

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import hashlib
import json

from app.database import get_db, Provider, Preset, Binding
from app.config import settings
from cyber_werewolves.models.llm_config import (
    CreateProviderRequest,
    CreatePresetRequest, 
    CreateBindingRequest,
    ModelResolution,
    Provider as ProviderModel,
    Preset as PresetModel,
    Binding as BindingModel
)

router = APIRouter()

# Provider Management (Admin Only)
@router.post("/admin/providers", response_model=ProviderModel)
async def create_provider(
    request: CreateProviderRequest,
    db: Session = Depends(get_db)
):
    """创建新的LLM服务提供商"""
    provider_id = f"prov-{uuid.uuid4().hex[:8]}"
    
    # Encrypt API key (in production, use proper encryption)
    encrypted_key = hashlib.sha256(request.api_key.encode()).hexdigest()
    
    provider = Provider(
        id=provider_id,
        name=request.name,
        type=request.type,
        base_url=str(request.base_url),
        api_key=encrypted_key,
        default_model=request.default_model,
        headers=request.headers or {},
        timeout_s=request.timeout_s,
        rate_limit_tpm=request.rate_limit_tpm,
        rate_limit_rpm=request.rate_limit_rpm,
        enabled=True
    )
    
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    return ProviderModel(
        id=provider.id,
        name=provider.name,
        type=provider.type,
        base_url=provider.base_url,
        api_key="[REDACTED]",  # Never return actual key
        default_model=provider.default_model,
        headers=provider.headers,
        timeout_s=provider.timeout_s,
        rate_limit_tpm=provider.rate_limit_tpm,
        rate_limit_rpm=provider.rate_limit_rpm,
        enabled=provider.enabled,
        created_at=provider.created_at
    )

@router.get("/admin/providers", response_model=List[ProviderModel])
async def list_providers(db: Session = Depends(get_db)):
    """获取所有LLM服务提供商（脱敏api_key）"""
    providers = db.query(Provider).all()
    
    return [
        ProviderModel(
            id=p.id,
            name=p.name,
            type=p.type,
            base_url=p.base_url,
            api_key="[REDACTED]",
            default_model=p.default_model,
            headers=p.headers,
            timeout_s=p.timeout_s,
            rate_limit_tpm=p.rate_limit_tpm,
            rate_limit_rpm=p.rate_limit_rpm,
            enabled=p.enabled,
            created_at=p.created_at
        ) for p in providers
    ]

@router.patch("/admin/providers/{provider_id}")
async def update_provider(
    provider_id: str,
    updates: dict,
    db: Session = Depends(get_db)
):
    """更新/启用/禁用Provider"""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Update allowed fields
    allowed_fields = ["name", "enabled", "timeout_s", "rate_limit_tpm", "rate_limit_rpm"]
    for field, value in updates.items():
        if field in allowed_fields:
            setattr(provider, field, value)
    
    db.commit()
    return {"status": "updated"}

@router.delete("/admin/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    db: Session = Depends(get_db)
):
    """删除Provider"""
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    db.delete(provider)
    db.commit()
    return {"status": "deleted"}

# Preset Management
@router.post("/admin/presets", response_model=PresetModel)
async def create_preset(
    request: CreatePresetRequest,
    db: Session = Depends(get_db)
):
    """创建模型预设"""
    preset_id = f"preset-{uuid.uuid4().hex[:8]}"
    
    # Validate provider exists
    provider = db.query(Provider).filter(Provider.id == request.provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    preset = Preset(
        id=preset_id,
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
    
    return PresetModel(
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

@router.get("/admin/presets", response_model=List[PresetModel])
async def list_presets(db: Session = Depends(get_db)):
    """获取所有模型预设"""
    presets = db.query(Preset).all()
    
    return [
        PresetModel(
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
        ) for p in presets
    ]

@router.delete("/admin/presets/{preset_id}")
async def delete_preset(
    preset_id: str,
    db: Session = Depends(get_db)
):
    """删除模型预设"""
    preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    db.delete(preset)
    db.commit()
    return {"status": "deleted"}

# Binding Management
@router.post("/admin/bindings", response_model=BindingModel)
async def create_binding(
    request: CreateBindingRequest,
    db: Session = Depends(get_db)
):
    """绑定预设到作用域"""
    binding_id = f"bind-{uuid.uuid4().hex[:8]}"
    
    # Validate preset exists
    preset = db.query(Preset).filter(Preset.id == request.preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    binding = Binding(
        id=binding_id,
        scope=request.scope,
        scope_key=request.scope_key,
        preset_id=request.preset_id,
        priority=request.priority
    )
    
    db.add(binding)
    db.commit()
    db.refresh(binding)
    
    return BindingModel(
        id=binding.id,
        scope=binding.scope,
        scope_key=binding.scope_key,
        preset_id=binding.preset_id,
        priority=binding.priority,
        created_at=binding.created_at
    )

@router.get("/admin/bindings", response_model=List[BindingModel])
async def list_bindings(
    scope: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """查询绑定规则"""
    query = db.query(Binding)
    if scope:
        query = query.filter(Binding.scope == scope)
    
    bindings = query.all()
    
    return [
        BindingModel(
            id=b.id,
            scope=b.scope,
            scope_key=b.scope_key,
            preset_id=b.preset_id,
            priority=b.priority,
            created_at=b.created_at
        ) for b in bindings
    ]

@router.delete("/admin/bindings/{binding_id}")
async def delete_binding(
    binding_id: str,
    db: Session = Depends(get_db)
):
    """删除绑定规则"""
    binding = db.query(Binding).filter(Binding.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")
    
    db.delete(binding)
    db.commit()
    return {"status": "deleted"}

# Core Resolution API
@router.get("/resolve-model", response_model=ModelResolution)
async def resolve_model(
    room_id: Optional[str] = None,
    seat: Optional[int] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """根据给定上下文解析最终生效的模型配置"""
    
    # Collect applicable bindings with priorities
    applicable_bindings = []
    
    # Global bindings (priority 0)
    global_bindings = db.query(Binding).filter(
        Binding.scope == "global"
    ).all()
    applicable_bindings.extend([(b, 0) for b in global_bindings])
    
    # Room bindings (priority 10)  
    if room_id:
        room_bindings = db.query(Binding).filter(
            Binding.scope == "room",
            Binding.scope_key == room_id
        ).all()
        applicable_bindings.extend([(b, 10) for b in room_bindings])
    
    # Seat bindings (priority 100)
    if seat:
        seat_bindings = db.query(Binding).filter(
            Binding.scope == "seat",
            Binding.scope_key == f"{room_id}-{seat}"
        ).all()
        applicable_bindings.extend([(b, 100) for b in seat_bindings])
    
    # Agent role bindings (priority based on binding.priority field)
    if role:
        role_bindings = db.query(Binding).filter(
            Binding.scope == "agent_role",
            Binding.scope_key == role
        ).all()
        applicable_bindings.extend([(b, b.priority) for b in role_bindings])
    
    # Sort by priority (highest first)
    applicable_bindings.sort(key=lambda x: x[1], reverse=True)
    
    if not applicable_bindings:
        raise HTTPException(status_code=404, detail="No applicable model configuration found")
    
    # Get the highest priority binding
    winning_binding = applicable_bindings[0][0]
    
    # Get the preset and provider
    preset = db.query(Preset).filter(Preset.id == winning_binding.preset_id).first()
    if not preset:
        raise HTTPException(status_code=500, detail="Preset not found")
    
    provider = db.query(Provider).filter(Provider.id == preset.provider_id).first()
    if not provider:
        raise HTTPException(status_code=500, detail="Provider not found")
    
    # Build resolution trace
    resolution_trace = []
    for binding, priority in applicable_bindings:
        resolution_trace.append({
            "scope": binding.scope,
            "scope_key": binding.scope_key,
            "preset_id": binding.preset_id,
            "priority": priority
        })
    
    return ModelResolution(
        provider={
            "id": provider.id,
            "type": provider.type,
            "base_url": provider.base_url
        },
        model_configuration={
            "model_id": preset.model_id,
            "temperature": preset.temperature / 100.0,
            "top_p": preset.top_p / 100.0,
            "max_tokens": preset.max_tokens,
            "tools_allowed": preset.tools_allowed
        },
        resolution_trace=resolution_trace
    )