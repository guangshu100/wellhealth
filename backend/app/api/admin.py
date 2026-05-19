"""
管理后台API
统计、Agent管理、评估管理、系统管理
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 数据库辅助函数 ============

def get_agents_from_db(status: str = None) -> List[dict]:
    """从数据库获取Agent列表"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            if status:
                result = db.execute(text("""
                SELECT id, name, type, description, status, version, 
                       created_at, updated_at, capabilities
                FROM agents 
                WHERE status = :status
            """), {"status": status})
            else:
                result = db.execute(text("""
                SELECT id, name, type, description, status, version, 
                       created_at, updated_at, capabilities
                FROM agents 
            """))
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get agents from database: {e}")
        return []


def get_agent_by_id_from_db(agent_id: str) -> dict:
    """从数据库获取单个Agent"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT id, name, type, description, status, version, 
                       created_at, updated_at, capabilities
                FROM agents 
                WHERE id = :id
            """), {"id": agent_id})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get agent from database: {e}")
        return None


# ============ Pydantic 模型 ============

class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"


class EvalStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# 内存存储（作为Fallback）
_agents: dict = {}
_evaluations: dict = {}
_sessions: dict = {}


def _init_admin_data():
    """初始化管理数据"""
    if _agents:
        return
    
    # Agent定义
    _agents["agent_diabetes"] = {
        "id": "agent_diabetes",
        "name": "糖尿病专科助手",
        "type": "diabetes",
        "description": "专注于糖尿病管理，提供血糖监测、用药指导、饮食建议",
        "status": "active",
        "version": "1.0.0",
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-03-15T10:00:00",
        "capabilities": ["血糖咨询", "用药指导", "饮食建议", "并发症筛查"],
        "conversation_count": 1250,
        "satisfaction": 4.7
    }
    _agents["agent_hypertension"] = {
        "id": "agent_hypertension",
        "name": "高血压专科助手",
        "type": "hypertension",
        "description": "专注于高血压管理，提供血压监测、生活方式干预、用药指导",
        "status": "active",
        "version": "1.0.0",
        "created_at": "2024-01-15T10:00:00",
        "updated_at": "2024-03-10T10:00:00",
        "capabilities": ["血压咨询", "用药指导", "运动建议", "限盐指导"],
        "conversation_count": 980,
        "satisfaction": 4.6
    }
    _agents["agent_nutrition"] = {
        "id": "agent_nutrition",
        "name": "营养师助手",
        "type": "nutrition",
        "description": "提供个性化营养方案，GI/GL计算，饮食记录分析",
        "status": "active",
        "version": "1.0.0",
        "created_at": "2024-01-20T10:00:00",
        "updated_at": "2024-03-05T10:00:00",
        "capabilities": ["营养咨询", "GI计算", "食谱推荐", "膳食分析"],
        "conversation_count": 650,
        "satisfaction": 4.8
    }
    _agents["agent_coach"] = {
        "id": "agent_coach",
        "name": "运动康复师",
        "type": "coach",
        "description": "制定个性化运动处方，跟踪运动数据，提供康复指导",
        "status": "active",
        "version": "1.0.0",
        "created_at": "2024-01-20T10:00:00",
        "updated_at": "2024-02-28T10:00:00",
        "capabilities": ["运动处方", "康复指导", "运动监测", "体能评估"],
        "conversation_count": 420,
        "satisfaction": 4.5
    }
    
    # 评估记录
    _evaluations["eval_001"] = {
        "id": "eval_001",
        "agent_type": "diabetes",
        "status": "completed",
        "total_cases": 100,
        "passed_cases": 92,
        "failed_cases": 8,
        "pass_rate": 0.92,
        "avg_response_time": 1.2,
        "created_at": "2024-03-10T10:00:00",
        "completed_at": "2024-03-10T10:15:00",
        "issues": [
            {"case": "用药剂量咨询", "severity": "medium", "description": "未明确提醒处方必要性"}
        ]
    }
    _evaluations["eval_002"] = {
        "id": "eval_002",
        "agent_type": "hypertension",
        "status": "completed",
        "total_cases": 100,
        "passed_cases": 88,
        "failed_cases": 12,
        "pass_rate": 0.88,
        "avg_response_time": 1.5,
        "created_at": "2024-03-12T10:00:00",
        "completed_at": "2024-03-12T10:18:00",
        "issues": [
            {"case": "紧急症状识别", "severity": "high", "description": "需加强胸痛症状的紧急处理指导"}
        ]
    }
    
    # 会话统计
    _sessions["s1"] = {
        "id": "s1",
        "patient_id": "p1",
        "agent_type": "diabetes",
        "message_count": 12,
        "duration": 1800,
        "created_at": "2024-03-15T10:00:00"
    }


_init_admin_data()


# ============ 统计数据 ============

@router.get("/stats")
async def get_stats():
    """获取系统统计"""
    return {
        "total_patients": 156,
        "total_doctors": 28,
        "total_conversations": 3850,
        "active_sessions": 42,
        "today_conversations": 125,
        "avg_response_time": 1.3,
        "system_health": "healthy",
        "trends": {
            "patients_growth": 12,
            "conversations_growth": 8,
            "satisfaction": 4.6
        }
    }


@router.get("/stats/overview")
async def get_stats_overview():
    """获取概览统计"""
    # 按疾病分布
    disease_distribution = {
        "diabetes": 68,
        "hypertension": 52,
        "hyperlipidemia": 28,
        "other": 18
    }
    
    # 按年龄分布
    age_distribution = {
        "30以下": 8,
        "30-40": 15,
        "40-50": 32,
        "50-60": 48,
        "60以上": 53
    }
    
    # 按Agent使用分布
    agent_usage = {
        "diabetes": 1250,
        "hypertension": 980,
        "nutrition": 650,
        "coach": 420,
        "general": 550
    }
    
    return {
        "disease_distribution": disease_distribution,
        "age_distribution": age_distribution,
        "agent_usage": agent_usage,
        "period": "近30天"
    }


@router.get("/stats/patients")
async def get_patient_stats():
    """获取患者统计"""
    return {
        "total": 156,
        "active": 128,
        "inactive": 28,
        "new_this_month": 15,
        "by_disease": {
            "diabetes": 68,
            "hypertension": 52,
            "both": 36
        },
        "by_gender": {
            "male": 82,
            "female": 74
        },
        "avg_age": 56.5
    }


@router.get("/stats/conversations")
async def get_conversation_stats():
    """获取会话统计"""
    return {
        "total": 3850,
        "today": 125,
        "this_week": 892,
        "this_month": 3250,
        "avg_duration": 180,
        "avg_messages": 8.5,
        "by_agent": {
            "diabetes": 1250,
            "hypertension": 980,
            "nutrition": 650,
            "coach": 420,
            "general": 550
        },
        "peak_hours": ["09:00-11:00", "14:00-16:00", "19:00-21:00"]
    }


# ============ Agent管理 ============

@router.get("/agents")
async def list_agents(status: Optional[str] = None):
    """获取Agent列表"""
    # 优先从数据库获取
    db_agents = get_agents_from_db(status)
    if db_agents:
        return {"items": db_agents, "total": len(db_agents)}
    
    # Fallback到内存存储
    agents = list(_agents.values())
    
    if status:
        agents = [a for a in agents if a["status"] == status]
    
    return {"items": agents, "total": len(agents)}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取Agent详情"""
    # 优先从数据库获取
    db_agent = get_agent_by_id_from_db(agent_id)
    if db_agent:
        return db_agent
    
    # Fallback到内存存储
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent不存在")
    return _agents[agent_id]


@router.post("/agents")
async def create_agent(agent_data: dict):
    """创建Agent"""
    agent_id = f"agent_{agent_data.get('type', 'custom')}_{len(_agents) + 1}"
    
    new_agent = {
        "id": agent_id,
        "name": agent_data.get("name", ""),
        "type": agent_data.get("type", "general"),
        "description": agent_data.get("description", ""),
        "status": "inactive",
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "capabilities": agent_data.get("capabilities", []),
        "conversation_count": 0,
        "satisfaction": 0
    }
    
    _agents[agent_id] = new_agent
    return new_agent


@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, agent_data: dict):
    """更新Agent"""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent不存在")
    
    existing = _agents[agent_id]
    for key, value in agent_data.items():
        if value is not None:
            existing[key] = value
    
    existing["updated_at"] = datetime.now().isoformat()
    _agents[agent_id] = existing
    
    return existing


@router.put("/agents/{agent_id}/status")
async def update_agent_status(agent_id: str, status: str):
    """更新Agent状态"""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent不存在")
    
    _agents[agent_id]["status"] = status
    _agents[agent_id]["updated_at"] = datetime.now().isoformat()
    
    return {"success": True, "status": status}


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """删除Agent"""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent不存在")
    
    del _agents[agent_id]
    return {"success": True}


# ============ 评估管理 ============

@router.get("/evaluations")
async def list_evaluations(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取评估列表"""
    evaluations = list(_evaluations.values())
    
    if agent_type:
        evaluations = [e for e in evaluations if e.get("agent_type") == agent_type]
    if status:
        evaluations = [e for e in evaluations if e.get("status") == status]
    
    return {
        "items": evaluations[skip:skip + limit],
        "total": len(evaluations)
    }


@router.get("/evaluations/{eval_id}")
async def get_evaluation(eval_id: str):
    """获取评估详情"""
    if eval_id not in _evaluations:
        raise HTTPException(status_code=404, detail="评估不存在")
    return _evaluations[eval_id]


@router.post("/evaluations")
async def create_evaluation(eval_data: dict):
    """创建评估任务"""
    eval_id = f"eval_{len(_evaluations) + 1:03d}"
    
    new_eval = {
        "id": eval_id,
        "agent_type": eval_data.get("agent_type", "diabetes"),
        "status": "pending",
        "total_cases": 0,
        "passed_cases": 0,
        "failed_cases": 0,
        "pass_rate": 0,
        "avg_response_time": 0,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "issues": []
    }
    
    _evaluations[eval_id] = new_eval
    
    # 模拟评估运行
    new_eval["status"] = "running"
    new_eval["total_cases"] = 100
    new_eval["passed_cases"] = 85 + (5 if eval_data.get("agent_type") == "diabetes" else 0)
    new_eval["failed_cases"] = 15 - (5 if eval_data.get("agent_type") == "diabetes" else 0)
    new_eval["pass_rate"] = new_eval["passed_cases"] / new_eval["total_cases"]
    new_eval["avg_response_time"] = 1.3
    new_eval["status"] = "completed"
    new_eval["completed_at"] = datetime.now().isoformat()
    
    return new_eval


@router.get("/evaluations/{eval_id}/report")
async def get_evaluation_report(eval_id: str):
    """获取评估报告"""
    if eval_id not in _evaluations:
        raise HTTPException(status_code=404, detail="评估不存在")
    
    eval_data = _evaluations[eval_id]
    
    return {
        "eval_id": eval_id,
        "agent_type": eval_data["agent_type"],
        "status": eval_data["status"],
        "summary": {
            "total_tests": eval_data["total_cases"],
            "passed": eval_data["passed_cases"],
            "failed": eval_data["failed_cases"],
            "pass_rate": eval_data["pass_rate"],
            "avg_response_time": eval_data["avg_response_time"]
        },
        "safety_assessment": {
            "level": "high" if eval_data["pass_rate"] > 0.9 else "medium",
            "violations": eval_data.get("issues", [])
        },
        "recommendations": [
            "继续加强安全红线检测",
            "优化紧急症状识别逻辑",
            "增加处方相关风险提示"
        ],
        "created_at": eval_data["created_at"],
        "completed_at": eval_data.get("completed_at")
    }


# ============ 系统管理 ============

@router.get("/system/health")
async def get_system_health():
    """获取系统健康状态"""
    return {
        "status": "healthy",
        "uptime": "15天 8小时",
        "cpu_usage": 35,
        "memory_usage": 62,
        "disk_usage": 45,
        "api_latency": {
            "p50": 120,
            "p95": 350,
            "p99": 800
        },
        "services": {
            "api": "healthy",
            "database": "healthy",
            "llm": "healthy",
            "vector_db": "degraded"
        },
        "last_check": datetime.now().isoformat()
    }


@router.get("/system/logs")
async def get_system_logs(
    level: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """获取系统日志"""
    logs = [
        {"level": "info", "message": "系统运行正常", "timestamp": "2024-03-15T10:00:00"},
        {"level": "info", "message": "用户登录: 张三", "timestamp": "2024-03-15T09:55:00"},
        {"level": "warning", "message": "API响应超时: /api/v1/chat/send", "timestamp": "2024-03-15T09:48:00"},
        {"level": "info", "message": "Agent调用: diabetes", "timestamp": "2024-03-15T09:45:00"},
        {"level": "error", "message": "向量数据库连接超时", "timestamp": "2024-03-15T09:30:00"},
    ]
    
    if level:
        logs = [l for l in logs if l["level"] == level]
    
    return {
        "items": logs[skip:skip + limit],
        "total": len(logs)
    }


@router.get("/system/config")
async def get_system_config():
    """获取系统配置"""
    return {
        "app_name": "康伴(WellHealth)",
        "version": "1.0.0",
        "environment": "production",
        "features": {
            "multi_agent": True,
            "rag": True,
            "simulation": True,
            "safety_check": True
        },
        "llm_providers": {
            "primary": "openai",
            "available": ["openai", "anthropic", "dashscope", "ollama"]
        },
        "data_retention_days": 90
    }


# ============ 用户管理 ============

@router.get("/users")
async def list_users(role: Optional[str] = None, skip: int = 0, limit: int = 20):
    """获取用户列表"""
    users = [
        {"id": "u1", "name": "管理员", "role": "admin", "email": "admin@wellhealth.com", "status": "active"},
        {"id": "u2", "name": "李医生", "role": "doctor", "email": "li@wellhealth.com", "status": "active"},
        {"id": "u3", "name": "王护士", "role": "nurse", "email": "wang@wellhealth.com", "status": "active"},
    ]
    
    if role:
        users = [u for u in users if u["role"] == role]
    
    return {"items": users[skip:skip + limit], "total": len(users)}


@router.post("/users/{user_id}/status")
async def update_user_status(user_id: str, status: str):
    """更新用户状态"""
    return {"success": True, "user_id": user_id, "status": status}
