"""动态 LLM 配置管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json
import asyncio
import time

from app.database import get_db
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class LLMConfigRequest(BaseModel):
    model_id: str
    api_key: Optional[str] = None
    base_url: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    timeout: Optional[int] = 30

class LLMConfigResponse(BaseModel):
    model_id: str
    base_url: str
    temperature: float
    max_tokens: int
    # 注意：不返回 api_key 和 timeout 以确保安全

class TestConnectionResponse(BaseModel):
    success: bool
    latency: Optional[int] = None
    model_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 内存中存储当前配置（生产环境应该使用数据库）
_current_configs: Dict[str, LLMConfigRequest] = {}

@router.post("/admin/llm/save-configs", response_model=Dict[str, str])
async def save_llm_configs(
    configs: Dict[str, LLMConfigRequest],
    current_user=Depends(get_current_user)
):
    """保存所有角色的 LLM 配置"""
    global _current_configs
    
    try:
        # 简单的验证
        for role, config in configs.items():
            if not config.model_id or not config.base_url:
                raise HTTPException(status_code=400, detail=f"角色 '{role}' 的 model_id 和 base_url 是必填项")
        
        _current_configs = configs
        
        logger.info(f"用户 {current_user.username} 保存了新的 LLM 配置")
        
        return {"message": "LLM配置已保存成功"}
        
    except Exception as e:
        logger.error(f"保存 LLM 配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")

@router.get("/admin/llm/get-configs", response_model=Dict[str, LLMConfigResponse])
async def get_llm_configs(current_user=Depends(get_current_user)):
    """获取所有角色的当前 LLM 配置"""
    
    if not _current_configs:
        # 如果没有配置，可以返回一个空字典或默认值
        return {}

    # 转换成不带 api_key 的响应模型
    response_configs = {}
    for role, config in _current_configs.items():
        response_configs[role] = LLMConfigResponse(
            model_id=config.model_id,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )

    return response_configs

@router.post("/admin/llm/test-config", response_model=TestConnectionResponse)
async def test_llm_config(
    config: LLMConfigRequest,
    current_user=Depends(get_current_user)
):
    """测试 LLM 配置连接"""
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 这里应该实际测试与 LLM 服务的连接
        # 由于我们要集成 Agno 的 OpenAIChat，这里先做一个简化的测试
        success, error_msg = await _test_llm_connection(config)
        
        # 计算延迟
        latency = int((time.time() - start_time) * 1000)
        
        if success:
            return TestConnectionResponse(
                success=True,
                latency=latency,
                model_info={
                    "model_id": config.model_id,
                    "base_url": config.base_url,
                    "status": "connected"
                }
            )
        else:
            return TestConnectionResponse(
                success=False,
                error=error_msg
            )
            
    except Exception as e:
        logger.error(f"测试 LLM 连接失败: {e}")
        return TestConnectionResponse(
            success=False,
            error=f"连接测试失败: {str(e)}"
        )

async def _test_llm_connection(config: LLMConfigRequest) -> tuple[bool, Optional[str]]:
    """测试与 LLM 服务的连接"""
    
    try:
        # 这里集成 Agno 的 OpenAIChat 进行实际测试
        from agno.models.openai import OpenAIChat
        
        # 创建 OpenAIChat 实例
        chat_model = OpenAIChat(
            id=config.model_id,
            base_url=config.base_url,
            api_key=config.api_key if config.api_key else None
        )
        
        # 发送一个简单的测试消息
        test_prompt = "请回复'测试成功'来验证连接。"
        
        # 使用 asyncio.wait_for 来设置超时
        response = await asyncio.wait_for(
            chat_model.arun(test_prompt),
            timeout=config.timeout or 30
        )
        
        if response and len(str(response)) > 0:
            logger.info(f"LLM 连接测试成功: {config.model_id}")
            return True, None
        else:
            return False, "模型响应为空"
            
    except asyncio.TimeoutError:
        return False, f"连接超时 ({config.timeout}秒)"
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg.lower():
            return False, "API Key 无效或未设置"
        elif "not found" in error_msg.lower():
            return False, "模型ID不存在"
        elif "unauthorized" in error_msg.lower():
            return False, "认证失败，请检查API Key"
        else:
            return False, f"连接失败: {error_msg}"