"""LLM Configuration models - implements D01 specification"""

from pydantic import BaseModel, AnyUrl, Field, SecretStr
from typing import Literal, Optional, Dict, List

class Provider(BaseModel):
    """定义一个 LLM 服务提供商"""
    id: str = Field(..., description="服务商唯一标识，如 'prov-openai-official'")
    name: str = Field(..., description="可读名称，如 'OpenAI 官方'")
    type: Literal["openai", "anthropic", "gemini", "openrouter", "vllm", "custom"] = Field(
        ..., description="服务商类型，用于适配不同的 API 协议"
    )
    base_url: AnyUrl = Field(..., description="API 的基础 URL")
    api_key: SecretStr = Field(..., description="API 密钥，将作为密文处理")
    default_model: str = Field(..., description="该服务商下的默认模型 ID")
    headers: Dict[str, str] = Field(default_factory=dict, description="自定义请求头")
    timeout_s: int = Field(default=60, description="API 请求超时时间（秒）")
    rate_limit_tpm: Optional[int] = Field(default=None, description="每分钟 Token 限流 (TPM)")
    rate_limit_rpm: Optional[int] = Field(default=None, description="每分钟请求数限流 (RPM)")
    enabled: bool = Field(default=True, description="是否启用该服务商")

class Preset(BaseModel):
    """定义一组可复用的模型及推理参数"""
    id: str = Field(..., description="预设集唯一标识，如 'preset-creative-wolf'")
    provider_id: str = Field(..., description="关联的 Provider ID")
    model_id: str = Field(..., description="要使用的具体模型 ID，如 'gpt-4o-mini'")
    name: str = Field(..., description="可读名称，如 '创意狼人发言风格'")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度，控制生成文本的随机性")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-P 采样")
    max_tokens: int = Field(default=2048, description="生成的最大 Token 数")
    seed: Optional[int] = Field(default=None, description="随机种子")
    stop: Optional[List[str]] = Field(default=None, description="停止序列")
    modalities: List[Literal["text", "vision", "audio"]] = Field(default=["text"], description="支持的模态")
    tools_allowed: bool = Field(default=True, description="是否允许此预设使用工具")
    vision_max_pixels: Optional[int] = Field(default=None, description="视觉模型最大像素数")

class Binding(BaseModel):
    """将预设集绑定到特定作用域"""
    id: str = Field(..., description="绑定规则的唯一标识")
    scope: Literal["global", "room", "seat", "agent_role"] = Field(..., description="作用域类型")
    scope_key: str = Field(..., description="作用域的键")
    preset_id: str = Field(..., description="要应用的 Preset ID")
    priority: int = Field(default=0, description="解析优先级，数字越大优先级越高")

class ModelResolution(BaseModel):
    """模型解析结果"""
    provider: Dict = Field(..., description="提供商信息")
    model_configuration: Dict = Field(..., description="模型配置")
    resolution_trace: List[Dict] = Field(..., description="解析追踪链")