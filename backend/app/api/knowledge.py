"""
知识库管理API
"""
import logging
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Pydantic 模型 ============

class KnowledgeCreate(BaseModel):
    title: str
    content: str
    type: str = "other"
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    author: Optional[str] = None
    status: str = "draft"


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    author: Optional[str] = None
    status: Optional[str] = None


class KnowledgeResponse(BaseModel):
    id: str
    title: str
    content: str
    type: str
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    author: Optional[str] = None
    status: str
    view_count: int = 0
    helpful_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


# ============ 数据库辅助函数 ============

def get_knowledge_list_from_db(
    search: str = None,
    knowledge_type: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 20
) -> List[dict]:
    """从数据库获取知识列表"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            conditions = []
            params = {"skip": skip, "limit": limit}
            
            if search:
                conditions.append("(title LIKE :search OR content LIKE :search)")
                params["search"] = f"%{search}%"
            
            if knowledge_type:
                conditions.append("type = :type")
                params["type"] = knowledge_type
            
            if status:
                conditions.append("status = :status")
                params["status"] = status
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            result = db.execute(text(f"""
                SELECT id, title, content, type, tags, source, author, status,
                       view_count, helpful_count, created_at, updated_at, published_at
                FROM knowledge_base 
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :skip
            """), params)
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get knowledge list from database: {e}")
        return []


def count_knowledge_from_db(search: str = None, knowledge_type: str = None, status: str = None) -> int:
    """统计知识数量"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            conditions = []
            params = {}
            
            if search:
                conditions.append("(title LIKE :search OR content LIKE :search)")
                params["search"] = f"%{search}%"
            
            if knowledge_type:
                conditions.append("type = :type")
                params["type"] = knowledge_type
            
            if status:
                conditions.append("status = :status")
                params["status"] = status
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            result = db.execute(text(f"""
                SELECT COUNT(*) as count FROM knowledge_base WHERE {where_clause}
            """), params)
            row = result.fetchone()
            return row[0] if row else 0
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to count knowledge: {e}")
        return 0


def get_knowledge_by_id_from_db(knowledge_id: str) -> dict:
    """从数据库获取单条知识"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            result = db.execute(text("""
                SELECT id, title, content, type, tags, source, author, status,
                       view_count, helpful_count, created_at, updated_at, published_at
                FROM knowledge_base 
                WHERE id = :id
            """), {"id": knowledge_id})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to get knowledge from database: {e}")
        return None


def create_knowledge_to_db(knowledge_data: dict) -> dict:
    """创建知识到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        import uuid
        db = SessionLocal()
        try:
            knowledge_id = f"kb{uuid.uuid4().hex[:8]}"
            now = datetime.now()
            
            tags_json = None
            if knowledge_data.get("tags"):
                import json
                tags_json = json.dumps(knowledge_data["tags"])
            
            db.execute(text("""
                INSERT INTO knowledge_base (id, title, content, type, tags, source, author, status, created_at, updated_at)
                VALUES (:id, :title, :content, :type, :tags, :source, :author, :status, :created_at, :updated_at)
            """), {
                "id": knowledge_id,
                "title": knowledge_data.get("title"),
                "content": knowledge_data.get("content"),
                "type": knowledge_data.get("type", "other"),
                "tags": tags_json,
                "source": knowledge_data.get("source"),
                "author": knowledge_data.get("author"),
                "status": knowledge_data.get("status", "draft"),
                "created_at": now,
                "updated_at": now
            })
            db.commit()
            return {**knowledge_data, "id": knowledge_id, "created_at": now, "updated_at": now}
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to create knowledge: {e}")
        return None


def update_knowledge_to_db(knowledge_id: str, knowledge_data: dict) -> dict:
    """更新知识到数据库"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        import json
        db = SessionLocal()
        try:
            now = datetime.now()
            
            updates = []
            params = {"id": knowledge_id, "updated_at": now}
            
            if "title" in knowledge_data:
                updates.append("title = :title")
                params["title"] = knowledge_data["title"]
            
            if "content" in knowledge_data:
                updates.append("content = :content")
                params["content"] = knowledge_data["content"]
            
            if "type" in knowledge_data:
                updates.append("type = :type")
                params["type"] = knowledge_data["type"]
            
            if "tags" in knowledge_data:
                updates.append("tags = :tags")
                params["tags"] = json.dumps(knowledge_data["tags"]) if knowledge_data["tags"] else None
            
            if "source" in knowledge_data:
                updates.append("source = :source")
                params["source"] = knowledge_data["source"]
            
            if "author" in knowledge_data:
                updates.append("author = :author")
                params["author"] = knowledge_data["author"]
            
            if "status" in knowledge_data:
                updates.append("status = :status")
                params["status"] = knowledge_data["status"]
                if knowledge_data["status"] == "published":
                    updates.append("published_at = :published_at")
                    params["published_at"] = now
            
            updates.append("updated_at = :updated_at")
            
            if not updates:
                return get_knowledge_by_id_from_db(knowledge_id)
            
            db.execute(text(f"""
                UPDATE knowledge_base 
                SET {', '.join(updates)}
                WHERE id = :id
            """), params)
            db.commit()
            return get_knowledge_by_id_from_db(knowledge_id)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to update knowledge: {e}")
        return None


def delete_knowledge_from_db(knowledge_id: str) -> bool:
    """从数据库删除知识"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM knowledge_base WHERE id = :id"), {"id": knowledge_id})
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to delete knowledge: {e}")
        return False


def increment_view_count(knowledge_id: str) -> bool:
    """增加查看次数"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("""
                UPDATE knowledge_base SET view_count = view_count + 1 WHERE id = :id
            """), {"id": knowledge_id})
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to increment view count: {e}")
        return False


def increment_helpful_count(knowledge_id: str) -> bool:
    """增加点赞次数"""
    try:
        from sqlalchemy import text
        from app.utils.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("""
                UPDATE knowledge_base SET helpful_count = helpful_count + 1 WHERE id = :id
            """), {"id": knowledge_id})
            db.commit()
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to increment helpful count: {e}")
        return False


# ============ 内存存储（Fallback）============

_knowledge_store = {}


def _init_sample_knowledge():
    """初始化示例知识"""
    if _knowledge_store:
        return
    
    sample_data = [
        {
            "id": "kb001",
            "title": "糖尿病饮食指南",
            "content": "糖尿病患者应遵循低糖、低脂、高纤维的饮食原则。建议每日摄入碳水化合物占总热量的50%-60%，蛋白质占15%-20%，脂肪占20%-30%。应少食多餐，避免一次性摄入过多碳水化合物。",
            "type": "disease",
            "tags": ["糖尿病", "饮食", "血糖控制"],
            "source": "中国糖尿病防治指南",
            "author": "李医生",
            "status": "published",
            "view_count": 156,
            "helpful_count": 45,
            "created_at": "2024-01-15T10:00:00",
            "updated_at": "2024-01-15T10:00:00"
        },
        {
            "id": "kb002",
            "title": "高血压患者运动处方",
            "content": "高血压患者适合进行有氧运动，如快走、慢跑、游泳、骑自行车等。每周至少150分钟中等强度运动或75分钟高强度运动。运动时应避免剧烈运动，运动前后测量血压。",
            "type": "exercise",
            "tags": ["高血压", "运动", "康复"],
            "source": "中国高血压防治指南",
            "author": "王医生",
            "status": "published",
            "view_count": 89,
            "helpful_count": 32,
            "created_at": "2024-01-20T10:00:00",
            "updated_at": "2024-01-20T10:00:00"
        },
        {
            "id": "kb003",
            "title": "二甲双胍用药指南",
            "content": "二甲双胍是2型糖尿病的一线用药。一般起始剂量为0.5g，每日2次，随餐服用。可根据血糖情况调整剂量，最大剂量不超过2g/天。常见不良反应包括胃肠道反应，通常随用药时间延长而减轻。",
            "type": "drug",
            "tags": ["二甲双胍", "糖尿病", "用药"],
            "source": "药品说明书",
            "author": "药师张",
            "status": "published",
            "view_count": 234,
            "helpful_count": 78,
            "created_at": "2024-02-01T10:00:00",
            "updated_at": "2024-02-01T10:00:00"
        },
        {
            "id": "kb004",
            "title": "低GI食物清单",
            "content": "GI值低于55的食物适合糖尿病患者食用。主要包括：燕麦、荞麦、全麦面包、糙米、红薯、苹果、梨、橙子、草莓、蓝莓、豆腐、花生等。",
            "type": "food",
            "tags": ["GI", "食物", "糖尿病饮食"],
            "source": "营养学资料",
            "author": "营养师李",
            "status": "published",
            "view_count": 312,
            "helpful_count": 98,
            "created_at": "2024-02-10T10:00:00",
            "updated_at": "2024-02-10T10:00:00"
        },
        {
            "id": "kb005",
            "title": "糖尿病筛查标准",
            "content": "建议40岁以上人群每年进行糖尿病筛查。有家族史、肥胖、高血压等高危人群应更早开始筛查。筛查指标包括空腹血糖、随机血糖和糖化血红蛋白(HbA1c)。",
            "type": "guideline",
            "tags": ["筛查", "糖尿病", "预防"],
            "source": "中国糖尿病防治指南",
            "author": "李医生",
            "status": "published",
            "view_count": 167,
            "helpful_count": 56,
            "created_at": "2024-02-15T10:00:00",
            "updated_at": "2024-02-15T10:00:00"
        }
    ]
    
    for item in sample_data:
        _knowledge_store[item["id"]] = item


_init_sample_knowledge()


# ============ API 路由 ============

@router.get("/")
async def list_knowledge(
    search: Optional[str] = None,
    type: Optional[str] = Query(None, alias="type"),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取知识列表"""
    # 优先从数据库获取
    items = get_knowledge_list_from_db(search, type, status, skip, limit)
    total = count_knowledge_from_db(search, type, status)
    
    if items:
        return {
            "items": items,
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit
        }
    
    # Fallback到内存存储
    results = list(_knowledge_store.values())
    
    if search:
        results = [r for r in results if search.lower() in r["title"].lower() or search.lower() in r["content"].lower()]
    if type:
        results = [r for r in results if r["type"] == type]
    if status:
        results = [r for r in results if r["status"] == status]
    
    total = len(results)
    items = results[skip:skip + limit]
    
    return {
        "items": items,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/{knowledge_id}")
async def get_knowledge(knowledge_id: str):
    """获取知识详情"""
    # 优先从数据库获取
    item = get_knowledge_by_id_from_db(knowledge_id)
    if item:
        increment_view_count(knowledge_id)
        return item
    
    # Fallback到内存存储
    if knowledge_id not in _knowledge_store:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    item = _knowledge_store[knowledge_id]
    item["view_count"] = item.get("view_count", 0) + 1
    return item


@router.post("/")
async def create_knowledge(knowledge: KnowledgeCreate):
    """创建知识"""
    knowledge_data = knowledge.dict()
    
    # 尝试写入数据库
    db_knowledge = create_knowledge_to_db(knowledge_data)
    if db_knowledge:
        return db_knowledge
    
    # Fallback到内存存储
    import uuid
    knowledge_id = f"kb{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    new_knowledge = {
        "id": knowledge_id,
        **knowledge_data,
        "view_count": 0,
        "helpful_count": 0,
        "created_at": now,
        "updated_at": now
    }
    _knowledge_store[knowledge_id] = new_knowledge
    return new_knowledge


@router.put("/{knowledge_id}")
async def update_knowledge(knowledge_id: str, knowledge: KnowledgeUpdate):
    """更新知识"""
    knowledge_data = {k: v for k, v in knowledge.dict().items() if v is not None}
    
    # 尝试更新数据库
    db_knowledge = update_knowledge_to_db(knowledge_id, knowledge_data)
    if db_knowledge:
        return db_knowledge
    
    # Fallback到内存存储
    if knowledge_id not in _knowledge_store:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    for key, value in knowledge_data.items():
        _knowledge_store[knowledge_id][key] = value
    
    _knowledge_store[knowledge_id]["updated_at"] = datetime.now().isoformat()
    return _knowledge_store[knowledge_id]


@router.delete("/{knowledge_id}")
async def delete_knowledge(knowledge_id: str):
    """删除知识"""
    # 尝试从数据库删除
    if delete_knowledge_from_db(knowledge_id):
        return {"success": True, "message": "删除成功"}
    
    # Fallback到内存存储
    if knowledge_id not in _knowledge_store:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    del _knowledge_store[knowledge_id]
    return {"success": True, "message": "删除成功"}


@router.post("/{knowledge_id}/helpful")
async def mark_helpful(knowledge_id: str):
    """点赞知识"""
    # 尝试更新数据库
    if increment_helpful_count(knowledge_id):
        item = get_knowledge_by_id_from_db(knowledge_id)
        return {"success": True, "helpful_count": item.get("helpful_count", 0) if item else 0}
    
    # Fallback到内存存储
    if knowledge_id not in _knowledge_store:
        raise HTTPException(status_code=404, detail="知识不存在")
    
    _knowledge_store[knowledge_id]["helpful_count"] = _knowledge_store[knowledge_id].get("helpful_count", 0) + 1
    return {"success": True, "helpful_count": _knowledge_store[knowledge_id]["helpful_count"]}


@router.get("/types/list")
async def get_knowledge_types():
    """获取知识类型列表"""
    return {
        "types": [
            {"value": "disease", "label": "疾病知识", "icon": "🏥"},
            {"value": "drug", "label": "用药知识", "icon": "💊"},
            {"value": "food", "label": "饮食知识", "icon": "🍎"},
            {"value": "exercise", "label": "运动知识", "icon": "🏃"},
            {"value": "guideline", "label": "指南规范", "icon": "📋"},
            {"value": "nursing", "label": "护理知识", "icon": "护理"},
            {"value": "other", "label": "其他", "icon": "📖"}
        ]
    }


@router.get("/search")
async def search_knowledge(
    query: str,
    knowledge_type: Optional[str] = Query(None, alias="type"),
    limit: int = 10
):
    """搜索知识"""
    items = get_knowledge_list_from_db(search=query, knowledge_type=knowledge_type, status="published", limit=limit)
    
    if not items:
        # Fallback到内存存储
        results = [r for r in _knowledge_store.values() 
                  if (query.lower() in r["title"].lower() or query.lower() in r["content"].lower())
                  and r.get("status") == "published"]
        items = results[:limit]
    
    return {"results": items, "total": len(items)}


@router.get("/recommendations/{patient_id}")
async def get_patient_recommendations(patient_id: str, limit: int = 5):
    """获取患者个性化知识推荐"""
    # 简化版：根据患者疾病推荐相关知识
    items = get_knowledge_list_from_db(status="published", limit=limit)
    
    return {"recommendations": items, "total": len(items)}
