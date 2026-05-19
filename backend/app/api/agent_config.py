import uuid
import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import inspect

from app.utils.database import get_db_session
from app.models.models import AgentLLMConfigModel
from app.services.agent_manager import AgentLoader
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    api_key: Optional[str] = None


class AgentConfigResponse(BaseModel):
    agent_type: str
    agent_name: str = ""
    agent_description: str = ""
    agent_emoji: str = "🤖"
    agent_color: str = "#409EFF"
    provider: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None
    api_key_hint: Optional[str] = None
    config_source: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SyncResult(BaseModel):
    synced: int
    skipped: int
    errors: List[str]


PROVIDER_MODELS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307", "claude-3-opus-20240229"],
    },
    "siliconflow": {
        "name": "SiliconFlow",
        "models": [
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct",
            "Qwen/Qwen2-7B-Instruct",
            "deepseek-ai/DeepSeek-V2.5",
        ],
    },
    "ollama": {
        "name": "Ollama",
        "models": ["llama3", "qwen2", "mistral", "gemma2"],
    },
    "dashscope": {
        "name": "DashScope",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max"],
    },
}


def _get_agent_metadata(agent_type: str) -> dict:
    try:
        loader = AgentLoader()
        agent_def = loader.load(agent_type)
        if agent_def and agent_def.metadata:
            return {
                "agent_name": agent_def.metadata.name,
                "agent_description": agent_def.metadata.description,
                "agent_emoji": agent_def.metadata.emoji,
                "agent_color": agent_def.metadata.color,
            }
    except Exception:
        pass
    return {
        "agent_name": agent_type,
        "agent_description": "",
        "agent_emoji": "🤖",
        "agent_color": "#409EFF",
    }


def _yaml_config_to_dict(agent_type: str, llm_config) -> dict:
    meta = _get_agent_metadata(agent_type)
    env_key_hint = _get_env_key_hint(llm_config.provider)
    return {
        "agent_type": agent_type,
        "agent_name": meta["agent_name"],
        "agent_description": meta["agent_description"],
        "agent_emoji": meta["agent_emoji"],
        "agent_color": meta["agent_color"],
        "provider": llm_config.provider,
        "model": llm_config.model,
        "temperature": llm_config.temperature,
        "max_tokens": llm_config.max_tokens,
        "timeout": llm_config.timeout,
        "fallback_provider": llm_config.fallback_provider,
        "fallback_model": llm_config.fallback_model,
        "api_key_hint": env_key_hint,
        "config_source": "yaml",
        "is_active": True,
        "created_at": None,
        "updated_at": None,
    }


def _get_env_key_hint(provider: str) -> Optional[str]:
    key = None
    if provider == "openai":
        key = settings.OPENAI_API_KEY
    elif provider == "anthropic":
        key = settings.ANTHROPIC_API_KEY
    elif provider == "dashscope":
        key = settings.DASHSCOPE_API_KEY
    elif provider == "siliconflow":
        key = settings.SILICONFLOW_API_KEY
    if key:
        return key[:8] + "..." if len(key) > 8 else key[:4] + "..."
    return None


def _db_row_to_dict(cfg: AgentLLMConfigModel) -> dict:
    api_key_hint = None
    if cfg.api_key:
        api_key_hint = cfg.api_key[:8] + "..." if len(cfg.api_key) > 8 else cfg.api_key[:4] + "..."
    return {
        "agent_type": cfg.agent_type,
        "provider": cfg.provider,
        "model": cfg.model,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "timeout": cfg.timeout,
        "fallback_provider": cfg.fallback_provider,
        "fallback_model": cfg.fallback_model,
        "api_key_hint": api_key_hint,
        "config_source": cfg.config_source,
        "is_active": cfg.is_active,
        "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
    }


def _enrich_with_metadata(raw: dict) -> dict:
    meta = _get_agent_metadata(raw["agent_type"])
    return {**raw, **meta}


def _ensure_table_exists():
    with get_db_session() as db:
        inspector = inspect(db.bind)
        if "agent_llm_configs" not in inspector.get_table_names():
            AgentLLMConfigModel.__table__.create(db.bind)
            logger.info("Created table agent_llm_configs")


@router.get("/agent-configs", response_model=List[AgentConfigResponse])
async def list_agent_configs():
    _ensure_table_exists()
    loader = AgentLoader()
    yaml_agents = loader.load_all()

    db_raw_map = {}
    with get_db_session() as db:
        rows = db.query(AgentLLMConfigModel).all()
        for row in rows:
            db_raw_map[row.agent_type] = _db_row_to_dict(row)

    result = []
    for agent_type, agent_def in yaml_agents.items():
        if agent_type in db_raw_map:
            result.append(_enrich_with_metadata(db_raw_map[agent_type]))
        else:
            result.append(_yaml_config_to_dict(agent_type, agent_def.llm_config))

    for agent_type, raw in db_raw_map.items():
        if agent_type not in yaml_agents:
            result.append(_enrich_with_metadata(raw))

    return result


@router.get("/agent-configs/providers/list")
async def list_providers():
    result = []
    for pid, pinfo in PROVIDER_MODELS.items():
        api_key = None
        if pid == "openai":
            api_key = settings.OPENAI_API_KEY
        elif pid == "anthropic":
            api_key = settings.ANTHROPIC_API_KEY
        elif pid == "dashscope":
            api_key = settings.DASHSCOPE_API_KEY
        elif pid == "siliconflow":
            api_key = settings.SILICONFLOW_API_KEY

        result.append({
            "id": pid,
            "name": pinfo["name"],
            "models": pinfo["models"],
            "configured": api_key is not None or pid == "ollama",
        })
    return {"providers": result}


@router.get("/agent-configs/env-info")
async def get_env_info():
    def mask_key(key: Optional[str]) -> Optional[str]:
        if not key:
            return None
        if len(key) <= 8:
            return key[:4] + "..."
        return key[:8] + "..."

    providers = []
    for pid, pinfo in PROVIDER_MODELS.items():
        api_key = None
        if pid == "openai":
            api_key = mask_key(settings.OPENAI_API_KEY)
        elif pid == "anthropic":
            api_key = mask_key(settings.ANTHROPIC_API_KEY)
        elif pid == "dashscope":
            api_key = mask_key(settings.DASHSCOPE_API_KEY)
        elif pid == "siliconflow":
            api_key = mask_key(settings.SILICONFLOW_API_KEY)

        providers.append({
            "id": pid,
            "name": pinfo["name"],
            "models": pinfo["models"],
            "configured": api_key is not None or pid == "ollama",
            "api_key_hint": api_key or ("本地部署" if pid == "ollama" else "未配置"),
        })

    return {
        "default_provider": settings.LLM_PROVIDER,
        "default_model": getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown"),
        "providers": providers,
    }


@router.get("/agent-configs/{agent_type}", response_model=AgentConfigResponse)
async def get_agent_config(agent_type: str):
    _ensure_table_exists()
    with get_db_session() as db:
        cfg = db.query(AgentLLMConfigModel).filter(
            AgentLLMConfigModel.agent_type == agent_type
        ).first()
        if cfg:
            return _enrich_with_metadata(_db_row_to_dict(cfg))

    loader = AgentLoader()
    agent_def = loader.load(agent_type)
    if not agent_def:
        raise HTTPException(status_code=404, detail=f"Agent类型 '{agent_type}' 不存在")

    return _yaml_config_to_dict(agent_type, agent_def.llm_config)


@router.put("/agent-configs/{agent_type}", response_model=AgentConfigResponse)
async def update_agent_config(agent_type: str, config: AgentConfigUpdate):
    _ensure_table_exists()
    loader = AgentLoader()
    yaml_def = loader.load(agent_type)

    with get_db_session() as db:
        cfg = db.query(AgentLLMConfigModel).filter(
            AgentLLMConfigModel.agent_type == agent_type
        ).first()

        if cfg:
            update_data = config.model_dump(exclude_none=True)
            for key, value in update_data.items():
                setattr(cfg, key, value)
            cfg.config_source = "database"
            cfg.updated_at = datetime.utcnow()
            db.flush()
            return _enrich_with_metadata(_db_row_to_dict(cfg))

        if yaml_def:
            llm = yaml_def.llm_config
            new_cfg = AgentLLMConfigModel(
                id=str(uuid.uuid4()),
                agent_type=agent_type,
                provider=config.provider or llm.provider,
                model=config.model or llm.model,
                temperature=config.temperature if config.temperature is not None else llm.temperature,
                max_tokens=config.max_tokens if config.max_tokens is not None else llm.max_tokens,
                timeout=config.timeout if config.timeout is not None else llm.timeout,
                fallback_provider=config.fallback_provider if config.fallback_provider is not None else llm.fallback_provider,
                fallback_model=config.fallback_model if config.fallback_model is not None else llm.fallback_model,
                config_source="database",
                is_active=True,
            )
        else:
            if not config.provider or not config.model:
                raise HTTPException(
                    status_code=400,
                    detail="新Agent配置必须指定 provider 和 model",
                )
            new_cfg = AgentLLMConfigModel(
                id=str(uuid.uuid4()),
                agent_type=agent_type,
                provider=config.provider,
                model=config.model,
                temperature=config.temperature if config.temperature is not None else 0.7,
                max_tokens=config.max_tokens if config.max_tokens is not None else 2000,
                timeout=config.timeout if config.timeout is not None else 120,
                fallback_provider=config.fallback_provider,
                fallback_model=config.fallback_model,
                config_source="database",
                is_active=True,
            )

        db.add(new_cfg)
        db.flush()
        return _enrich_with_metadata(_db_row_to_dict(new_cfg))


@router.post("/agent-configs/sync-from-yaml", response_model=SyncResult)
async def sync_from_yaml():
    _ensure_table_exists()
    loader = AgentLoader()
    yaml_agents = loader.load_all()

    synced = 0
    skipped = 0
    errors = []

    with get_db_session() as db:
        for agent_type, agent_def in yaml_agents.items():
            try:
                existing = db.query(AgentLLMConfigModel).filter(
                    AgentLLMConfigModel.agent_type == agent_type
                ).first()

                if existing:
                    skipped += 1
                    continue

                llm = agent_def.llm_config
                new_cfg = AgentLLMConfigModel(
                    id=str(uuid.uuid4()),
                    agent_type=agent_type,
                    provider=llm.provider,
                    model=llm.model,
                    temperature=llm.temperature,
                    max_tokens=llm.max_tokens,
                    timeout=llm.timeout,
                    fallback_provider=llm.fallback_provider,
                    fallback_model=llm.fallback_model,
                    config_source="database",
                    is_active=True,
                )
                db.add(new_cfg)
                synced += 1
            except Exception as e:
                errors.append(f"{agent_type}: {str(e)}")

    return SyncResult(synced=synced, skipped=skipped, errors=errors)


@router.post("/agent-configs/{agent_type}/reset")
async def reset_agent_config(agent_type: str):
    _ensure_table_exists()
    with get_db_session() as db:
        cfg = db.query(AgentLLMConfigModel).filter(
            AgentLLMConfigModel.agent_type == agent_type
        ).first()

        if not cfg:
            raise HTTPException(
                status_code=404,
                detail=f"Agent类型 '{agent_type}' 无数据库配置，无需重置",
            )

        db.delete(cfg)

    loader = AgentLoader()
    agent_def = loader.load(agent_type)
    if agent_def:
        return _yaml_config_to_dict(agent_type, agent_def.llm_config)

    return {"message": f"Agent '{agent_type}' 数据库配置已删除"}


class TestConnectionRequest(BaseModel):
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 100


@router.post("/agent-configs/test-connection")
async def test_llm_connection(request: TestConnectionRequest):
    from app.services.llm_client import LLMClient
    import time

    start = time.time()
    try:
        client = LLMClient(provider=request.provider, model=request.model)
        response = await client.chat_with_system(
            system_prompt="You are a helpful assistant.",
            user_message="Say hello in one word.",
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        elapsed = round(time.time() - start, 2)

        if response and "AI服务暂时不可用" in response:
            error_detail = response.replace("抱歉，AI服务暂时不可用: ", "")
            return {
                "success": False,
                "provider": request.provider,
                "model": request.model,
                "elapsed_seconds": elapsed,
                "error": error_detail,
                "message": f"连接失败: {error_detail}",
            }

        return {
            "success": True,
            "provider": request.provider,
            "model": request.model,
            "response_preview": response[:200] if response else "",
            "elapsed_seconds": elapsed,
            "message": f"连接成功，响应时间 {elapsed}s",
        }
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        return {
            "success": False,
            "provider": request.provider,
            "model": request.model,
            "elapsed_seconds": elapsed,
            "error": str(e),
            "message": f"连接失败: {str(e)}",
        }
