"""
聊天API
多Agent协作问答
"""

import uuid
import json
import logging
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime

from app.services.agent_manager import (
    AgentSelector,
    AgentType,
    AgentDefinition,
    AgentLoader,
    IntelligentAgentSelector,
)
from app.config import settings
from app.services.agent_executor import (
    agent_executor,
    session_manager,
    AgentContext,
    ExecutionResult,
    agent_dialogue_manager,
)
from app.services.knowledge_base import knowledge_manager
from app.services.safety_checker import SafetyChecker
from sqlalchemy import text
from app.utils.db_operations import execute_query, execute_update, execute_in_session

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 数据库辅助函数 ============


def save_chat_session_to_db(
    session_id: str, patient_id: str = None, title: str = None, agent_type: str = None
) -> bool:
    try:
        return execute_update(
            """
            INSERT INTO chat_sessions (id, patient_id, agent_type, title, status, message_count, created_at, updated_at)
            VALUES (:id, :patient_id, :agent_type, :title, 'active', 0, :now, :now)
            ON DUPLICATE KEY UPDATE title = :title, updated_at = :now
        """,
            {
                "id": session_id,
                "patient_id": patient_id,
                "agent_type": agent_type,
                "title": title or "新对话",
                "now": datetime.now(),
            },
        )
    except Exception as e:
        logger.warning(f"Failed to save session to database: {e}")
        return False


def save_message_to_db(
    session_id: str,
    role: str,
    content: str,
    agent_type: str = None,
    sources: List[Dict] = None,
    safety_level: str = None,
) -> bool:
    try:
        message_id = f"msg{uuid.uuid4().hex[:12]}"
        now = datetime.now()
        sources_json = json.dumps(sources) if sources else None

        insert_params = {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "agent_type": agent_type,
            "sources": sources_json,
            "safety_level": safety_level,
            "created_at": now,
        }
        update_params = {"session_id": session_id, "now": now}

        def _save(db):
            db.execute(
                text("""
                INSERT INTO chat_messages (id, session_id, role, content, agent_type, sources, safety_level, created_at)
                VALUES (:id, :session_id, :role, :content, :agent_type, :sources, :safety_level, :created_at)
            """),
                insert_params,
            )
            db.execute(
                text("""
                UPDATE chat_sessions 
                SET message_count = message_count + 1, updated_at = :now 
                WHERE id = :session_id
            """),
                update_params,
            )
            return True

        result = execute_in_session(_save)
        return result if result is not None else False
    except Exception as e:
        logger.warning(f"Failed to save message to database: {e}")
        return False


def get_chat_history_from_db(session_id: str) -> List[Dict]:
    try:
        rows = execute_query(
            """
            SELECT id, role, content, agent_type, sources, safety_level, created_at
            FROM chat_messages 
            WHERE session_id = :session_id
            ORDER BY created_at ASC
        """,
            {"session_id": session_id},
        )
        if rows is None:
            return []
        messages = []
        for msg in rows:
            if msg.get("sources"):
                try:
                    msg["sources"] = json.loads(msg["sources"])
                except:
                    msg["sources"] = []
            messages.append(msg)
        return messages
    except Exception as e:
        logger.warning(f"Failed to get chat history from database: {e}")
        return []


def get_sessions_from_db(patient_id: str = None, limit: int = 20) -> List[Dict]:
    try:
        if patient_id:
            rows = execute_query(
                """
                SELECT id, patient_id, agent_type, title, status, message_count, created_at, updated_at
                FROM chat_sessions 
                WHERE patient_id = :patient_id
                ORDER BY updated_at DESC
                LIMIT :limit
            """,
                {"patient_id": patient_id, "limit": limit},
            )
        else:
            rows = execute_query(
                """
                SELECT id, patient_id, agent_type, title, status, message_count, created_at, updated_at
                FROM chat_sessions 
                ORDER BY updated_at DESC
                LIMIT :limit
            """,
                {"limit": limit},
            )
        return rows if rows is not None else []
    except Exception as e:
        logger.warning(f"Failed to get sessions from database: {e}")
        return []


def update_session_title(session_id: str, title: str) -> bool:
    try:
        return execute_update(
            """
            UPDATE chat_sessions SET title = :title, updated_at = :now WHERE id = :id
        """,
            {"id": session_id, "title": title, "now": datetime.now()},
        )
    except Exception as e:
        logger.warning(f"Failed to update session title: {e}")
        return False


class ChatMessage(BaseModel):
    """聊天消息"""

    session_id: Optional[str] = None
    patient_id: Optional[str] = None
    message: str
    agent_type: Optional[str] = None
    use_rag: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""

    session_id: str
    message: str
    agent_type: str
    sources: List[Dict] = []
    safety: Optional[Dict] = None


class AgentSelectRequest(BaseModel):
    """Agent选择请求"""

    patient_id: Optional[str] = None
    query: str
    patient_context: Optional[Dict] = None


class SessionCreateRequest(BaseModel):
    """创建会话请求"""

    patient_id: Optional[str] = None


class SessionUpdateRequest(BaseModel):
    """更新会话请求"""

    title: Optional[str] = None


@router.post("/send", response_model=ChatResponse)
async def send_message(chat: ChatMessage):
    """
    发送消息并获取回复
    """
    # 获取或创建会话
    session_id = chat.session_id
    if session_id is None:
        session_id = session_manager.create_session(chat.patient_id or "anonymous")

    # 保存会话到数据库，使用消息前20字符作为标题
    session_title = chat.message[:20] + "..." if len(chat.message) > 20 else chat.message
    save_chat_session_to_db(session_id, chat.patient_id, session_title, chat.agent_type)

    # 获取上下文
    context = session_manager.get_session(session_id)
    if context is None:
        context = AgentContext(patient_id=chat.patient_id, session_id=session_id)

    # 添加用户消息到历史
    session_manager.add_message(session_id, "user", chat.message)

    # 保存用户消息到数据库
    save_message_to_db(session_id, "user", chat.message, chat.agent_type)

    # 执行问答
    if chat.use_rag:
        result = await agent_executor.execute_with_rag(
            query=chat.message, context=context, agent_type=chat.agent_type
        )
    else:
        result = await agent_executor.execute(
            query=chat.message, context=context, agent_type=chat.agent_type
        )

    # 添加AI回复到历史
    session_manager.add_message(session_id, "assistant", result.response)

    logger.info(
        f"Chat response - agent_type: {result.agent_type}, response length: {len(result.response)}, response: {result.response[:200] if result.response else 'EMPTY'}"
    )

    # 保存AI回复到数据库
    safety_level = result.safety_result.get("level") if result.safety_result else None
    save_message_to_db(
        session_id, "assistant", result.response, result.agent_type, result.sources, safety_level
    )

    # 如果是第一条消息，更新会话标题
    history = session_manager.get_history(session_id)
    if len(history) <= 2:  # user + assistant
        title = chat.message[:30] + "..." if len(chat.message) > 30 else chat.message
        update_session_title(session_id, title)

    return ChatResponse(
        session_id=session_id,
        message=result.response,
        agent_type=result.agent_type,
        sources=result.sources,
        safety=result.safety_result,
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    获取对话历史 - 优先从数据库获取
    """
    # 优先从数据库获取
    db_history = get_chat_history_from_db(session_id)
    if db_history:
        return {
            "session_id": session_id,
            "messages": db_history,
            "count": len(db_history),
            "source": "database",
        }

    # Fallback到内存
    history = session_manager.get_history(session_id)
    return {
        "session_id": session_id,
        "messages": history,
        "count": len(history),
        "source": "memory",
    }


@router.get("/sessions")
async def list_sessions(patient_id: str = None, limit: int = 20):
    """
    获取会话列表
    """
    sessions = get_sessions_from_db(patient_id, limit)
    return {"sessions": sessions, "count": len(sessions)}


@router.post("/agent/select")
async def select_agent(request: AgentSelectRequest):
    """
    选择合适的Agent
    """
    selector = AgentSelector()

    # 如果有患者上下文，优先使用
    patient_context = request.patient_context
    if patient_context is None and request.patient_id:
        # TODO: 从数据库获取患者信息
        patient_context = {}

    # 选择Agent
    agent_type = selector.select(request.query, patient_context)
    agent_def = selector.get_agent_definition(agent_type)

    return {
        "agent_type": agent_type,
        "agent_name": agent_def.metadata.name if agent_def else None,
        "description": agent_def.metadata.description if agent_def else None,
        "emoji": agent_def.metadata.emoji if agent_def else None,
        "color": agent_def.metadata.color if agent_def else None,
    }


@router.get("/agents")
async def list_agents(check_status: bool = False):
    selector = AgentSelector()
    agents = selector.get_all_agents()

    if check_status:
        from app.services.llm_client import LLMClient
        import asyncio

        async def _check(agent_info: dict) -> dict:
            agent_type = agent_info["type"]
            try:
                loader = AgentLoader()
                agent_def = loader.load(agent_type)
                if not agent_def:
                    return {**agent_info, "status": "offline", "status_reason": "Agent定义未找到"}

                llm_config = agent_def.llm_config
                provider = llm_config.provider if llm_config.provider != "default" else settings.LLM_PROVIDER
                model = llm_config.model if llm_config.model != "default" else getattr(settings, f"{provider.upper()}_MODEL", "")

                client = LLMClient(provider=provider, model=model)
                response = await client.chat_with_system(
                    system_prompt="You are a health assistant.",
                    user_message="Hi",
                    temperature=0.7,
                    max_tokens=10,
                )

                if response and "AI服务暂时不可用" in response:
                    error_msg = response.replace("抱歉，AI服务暂时不可用: ", "")
                    return {**agent_info, "status": "offline", "status_reason": error_msg}

                return {**agent_info, "status": "online", "status_reason": None}
            except Exception as e:
                return {**agent_info, "status": "offline", "status_reason": str(e)}

        tasks = [_check(a) for a in agents]
        agents = await asyncio.gather(*tasks)

    return {"agents": agents, "count": len(agents)}


@router.post("/session/create")
async def create_session(request: SessionCreateRequest):
    """
    创建新会话
    """
    session_id = session_manager.create_session(request.patient_id)

    # 保存会话到数据库
    save_chat_session_to_db(session_id, request.patient_id, "新对话", None)

    return {"session_id": session_id, "patient_id": request.patient_id}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    """
    # 从内存中删除
    session_manager.delete_session(session_id)

    def _delete(db):
        db.execute(text("DELETE FROM chat_messages WHERE session_id = :id"), {"id": session_id})
        db.execute(text("DELETE FROM chat_sessions WHERE id = :id"), {"id": session_id})
        return True

    execute_in_session(_delete)

    return {"success": True, "message": "会话已删除"}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    获取会话信息
    """
    context = session_manager.get_session(session_id)
    if context is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session_id,
        "patient_id": context.patient_id,
        "message_count": len(context.messages),
        "created_at": context.messages[0].timestamp.isoformat() if context.messages else None,
    }


@router.put("/session/{session_id}")
async def update_session(session_id: str, request: SessionUpdateRequest):
    """
    更新会话
    """
    if request.title:
        update_session_title(session_id, request.title)
    return {"success": True}


@router.post("/multi-agent")
async def multi_agent_chat(chat: ChatMessage):
    """
    多Agent会诊模式 - 返回各Agent结果和综合结果
    """
    session_id = chat.session_id or session_manager.create_session(chat.patient_id)

    # 保存会话到数据库
    session_title = chat.message[:20] + "..." if len(chat.message) > 20 else chat.message
    save_chat_session_to_db(session_id, chat.patient_id, session_title, "multi")

    # 保存用户消息到数据库
    save_message_to_db(session_id, "user", chat.message, "multi")

    context = session_manager.get_session(session_id)

    if context is None:
        context = AgentContext(patient_id=chat.patient_id, session_id=session_id)

    # 添加用户消息到上下文
    session_manager.add_message(session_id, "user", chat.message)

    # 执行多Agent会诊
    results = await agent_executor.multi_agent_consultation(query=chat.message, context=context)

    # Agent中文名称映射
    agent_names = {
        "diabetes": "糖尿病专家",
        "nutrition": "营养师",
        "coach": "运动健康教练",
        "hypertension": "高血压专家",
        "medication": "用药顾问",
        "psychology": "心理健康顾问",
        "rehabilitation": "康复专家",
        "general": "健康助手",
    }

    # 生成综合回复
    summary_response = ""
    try:
        from app.services.llm_client import get_llm_client

        # 提取各Agent的核心观点摘要（而非完整回答），避免prompt过长导致模型乱码
        agent_summaries = []
        for r in results:
            # 截取每个Agent回答的前500字作为核心观点
            resp = r.response
            if len(resp) > 500:
                resp = resp[:500] + "..."
            agent_summaries.append(f"【{agent_names.get(r.agent_type, r.agent_type)}】: {resp}")
        all_summaries = "\n\n".join(agent_summaries)

        summary_prompt = f"""用户问题：{chat.message}

以下是各位专家的核心意见摘要：

{all_summaries}

请综合以上专家意见，输出一份结构清晰的综合建议。要求：
1. 按类别组织：饮食调整、运动计划、药物调整、监测随访、注意事项
2. 每个类别列出2-3条关键建议，简洁明了
3. 药物名称、数值等关键信息必须准确完整
4. 最后附上温馨提醒

请直接输出综合建议："""

        summary_response = await get_llm_client().chat_with_system(
            system_prompt="你是一位专业健康顾问，请综合多位专家意见，输出准确、简洁、结构化的健康建议。注意：药物名称和数值必须准确无误，不要编造或篡改。",
            user_message=summary_prompt,
            temperature=0.3,
            max_tokens=3000,
        )
    except Exception as e:
        logger.warning(f"Failed to generate summary: {e}")
        # 降级方案：直接拼接各agent的回答
        summary_response = "\n\n".join(
            [f"【{agent_names.get(r.agent_type, r.agent_type)}】\n{r.response}" for r in results]
        )
        summary_response = "以下是各位专家的综合建议：\n\n" + summary_response

    # 保存各Agent的回复到数据库
    for r in results:
        agent_content = f"【{agent_names.get(r.agent_type, r.agent_type)}】{r.response}"
        save_message_to_db(session_id, "assistant", agent_content, r.agent_type, r.sources)

    # 保存综合建议到数据库
    save_message_to_db(session_id, "assistant", summary_response, "summary")

    # 添加AI回复到上下文
    session_manager.add_message(session_id, "assistant", summary_response)

    return {
        "session_id": session_id,
        "query": chat.message,
        "individual_results": [
            {
                "agent_type": r.agent_type,
                "agent_name": agent_names.get(r.agent_type, r.agent_type),  # 添加中文名称
                "response": r.response,
                "sources": r.sources,
                "safety": r.safety_result,
            }
            for r in results
        ],
        "summary": summary_response,
    }


@router.post("/safety/check")
async def check_safety(text: str):
    """
    检查文本安全性
    """
    checker = SafetyChecker()
    result = checker.check(text)

    return {
        "safe": result.safe,
        "level": result.level.value,
        "violations": result.violations,
        "suggestions": result.suggestions,
    }


@router.post("/disclaimer/add")
async def add_disclaimer(text: str):
    """
    为文本添加免责声明
    """
    checker = SafetyChecker()
    result = checker.add_disclaimer(text)
    return {"text": result}


class AgentDialogueRequest(BaseModel):
    """Agent对话请求"""

    message: str
    patient_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_types: Optional[List[str]] = None
    max_turns: int = 2


@router.get("/agent-dialogue/stream")
async def agent_dialogue_stream(
    message: str,
    patient_id: str = None,
    session_id: str = None,
    agent_types: str = None,
    max_turns: int = 2,
):
    """
    Agent对话模式 - SSE流式输出 (GET)
    """
    import json

    query = message

    logger.info(f"[AgentDialogueStream] Starting for query: {query[:30]}...")

    async def generate():
        # 创建selector实例
        selector = AgentSelector()
        intelligent_selector = IntelligentAgentSelector()

        # 解析agent_types参数
        agent_types_param = agent_types
        local_agent_types_list = []
        if agent_types_param:
            try:
                local_agent_types_list = json.loads(agent_types_param)
            except:
                local_agent_types_list = []

        # 如果没有指定Agent，使用LLM智能选择
        if not local_agent_types_list:
            logger.info("[AgentDialogueStream] No agents specified, using intelligent selection...")
            local_agent_types_list = await intelligent_selector.select_agents(
                query=query, patient_context={"patient_id": patient_id} if patient_id else None
            )
            logger.info(f"[AgentDialogueStream] LLM selected agents: {local_agent_types_list}")

        sid = session_id or session_manager.create_session(patient_id)

        # 保存会话，使用用户消息的前20个字符作为标题
        session_title = query[:20] + "..." if len(query) > 20 else query
        save_chat_session_to_db(sid, patient_id, session_title, "dialogue")

        context = session_manager.get_session(sid)
        if context is None:
            context = AgentContext(patient_id=patient_id, session_id=sid)

        # 保存用户消息
        save_message_to_db(sid, "user", query, "dialogue")

        actual_max_turns = max_turns or 2

        agent_names = {}
        for agent_type in local_agent_types_list:
            agent_def = selector.get_agent_definition(agent_type)
            agent_names[agent_type] = agent_def.metadata.name if agent_def else agent_type

        all_turns = []

        # 第一轮：所有Agent回答用户问题
        yield f"data: {json.dumps({'type': 'start', 'message': '开始Agent对话...'})}\n\n"

        for i, agent_type in enumerate(local_agent_types_list):
            agent_def = selector.get_agent_definition(agent_type)
            if agent_def is None:
                continue

            yield f"data: {json.dumps({'type': 'agent_start', 'agent_type': agent_type, 'agent_name': agent_names[agent_type]})}\n\n"

            try:
                result = await agent_executor.execute(query, context, agent_type)

                turn_data = {
                    "turn_index": 0,
                    "speaker_agent": agent_type,
                    "speaker_name": agent_names[agent_type],
                    "content": result.response,
                    "sources": result.sources,
                }
                all_turns.append(turn_data)

                yield f"data: {json.dumps({'type': 'agent_response', **turn_data})}\n\n"

            except Exception as e:
                logger.error(f"Agent {agent_type} error: {e}")
                yield f"data: {json.dumps({'type': 'agent_error', 'agent_type': agent_type, 'error': str(e)})}\n\n"

        # 后续轮次：Agent之间讨论
        for turn_idx in range(1, actual_max_turns):
            yield f"data: {json.dumps({'type': 'round_start', 'round': turn_idx + 1})}\n\n"

            for i, agent_type in enumerate(local_agent_types_list):
                agent_def = selector.get_agent_definition(agent_type)
                if agent_def is None:
                    continue

                dialogue_history = "\n\n".join(
                    [f"【{t['speaker_name']}】{t['content']}" for t in all_turns]
                )

                prompt = f"""你是一位专业的医疗健康顾问。请阅读以下多位专家的讨论，然后从你的专业角度给出你的观点和建议。

讨论历史：
{dialogue_history}

请给出你的专业建议和观点。"""

                yield f"data: {json.dumps({'type': 'agent_start', 'agent_type': agent_type, 'agent_name': agent_names[agent_type], 'round': turn_idx + 1})}\n\n"

                try:
                    result = await agent_executor.execute(prompt, context, agent_type)

                    turn_data = {
                        "turn_index": turn_idx,
                        "speaker_agent": agent_type,
                        "speaker_name": agent_names[agent_type],
                        "content": result.response,
                        "sources": result.sources,
                    }
                    all_turns.append(turn_data)

                    yield f"data: {json.dumps({'type': 'agent_response', **turn_data})}\n\n"

                except Exception as e:
                    logger.error(f"Agent {agent_type} round {turn_idx} error: {e}")
                    yield f"data: {json.dumps({'type': 'agent_error', 'agent_type': agent_type, 'error': str(e)})}\n\n"

        # Agent中文名称映射
        dialogue_agent_names = {
            "diabetes": "糖尿病专家",
            "nutrition": "营养师",
            "coach": "运动健康教练",
            "hypertension": "高血压专家",
            "medication": "用药顾问",
            "psychology": "心理健康顾问",
            "rehabilitation": "康复专家",
            "general": "健康助手",
        }

        # 生成总结
        yield f"data: {json.dumps({'type': 'summary_start'})}\n\n"

        try:
            # 提取各Agent核心观点摘要（而非完整回答），避免prompt过长导致模型乱码
            turn_summaries = []
            for t in all_turns:
                content = t['content']
                if len(content) > 500:
                    content = content[:500] + "..."
                turn_summaries.append(f"【{t['speaker_name']}】: {content}")
            dialogue_text = "\n\n".join(turn_summaries)

            summary_prompt = f"""用户问题：{query}

以下是各位专家的核心意见摘要：

{dialogue_text}

请综合以上专家意见，输出一份结构清晰的综合建议。要求：
1. 按类别组织：饮食调整、运动计划、药物调整、监测随访、注意事项
2. 每个类别列出2-3条关键建议，简洁明了
3. 药物名称、数值等关键信息必须准确完整
4. 最后附上温馨提醒

请直接输出综合建议："""

            from app.services.llm_client import get_llm_client

            summary = await get_llm_client().chat_with_system(
                system_prompt="你是一位专业健康顾问，请综合多位专家意见，输出准确、简洁、结构化的健康建议。注意：药物名称和数值必须准确无误，不要编造或篡改。",
                user_message=summary_prompt,
                temperature=0.3,
                max_tokens=3000,
            )
        except Exception as e:
            logger.error(f"Summary error: {e}")
            # 降级方案：直接拼接各agent的回答
            summary = "\n\n".join(
                [f"【{turn['speaker_name']}】\n{turn['content']}" for turn in all_turns]
            )
            summary = "以下是各位专家的综合建议：\n\n" + summary

        yield f"data: {json.dumps({'type': 'summary', 'summary': summary})}\n\n"

        # 保存各Agent的回答到数据库
        for turn in all_turns:
            save_message_to_db(
                sid,
                "assistant",
                f"【{turn['speaker_name']}】{turn['content']}",
                turn["speaker_agent"],
                turn["sources"],
            )

        # 保存综合建议到数据库
        save_message_to_db(sid, "assistant", summary, "summary")

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/agent-dialogue/{dialogue_id}")
async def get_agent_dialogue(dialogue_id: str):
    """
    获取Agent对话详情
    """
    turns = agent_dialogue_manager.get_dialogue(dialogue_id)

    if not turns:
        return {"dialogue_id": dialogue_id, "turns": [], "summary": ""}

    return {
        "dialogue_id": dialogue_id,
        "turns": [
            {
                "turn_index": turn.turn_index,
                "speaker_agent": turn.speaker_agent,
                "speaker_name": turn.speaker_name,
                "content": turn.content,
                "sources": turn.sources,
            }
            for turn in turns
        ],
    }


class SingleAgentRequest(BaseModel):
    """单个Agent回答请求"""

    message: str
    agent_type: str
    patient_id: Optional[str] = None
    use_rag: bool = True


class SummaryRequest(BaseModel):
    """总结请求"""

    query: str
    agent_results: List[Dict[str, str]]


@router.post("/single-agent")
async def single_agent_answer(request: SingleAgentRequest):
    """
    单个Agent回答问题 - 用于分步请求
    """
    logger.info(f"[SingleAgent] agent_type: {request.agent_type}, query: {request.message[:30]}...")

    context = AgentContext(patient_id=request.patient_id)

    if request.use_rag:
        result = await agent_executor.execute_with_rag(
            query=request.message, context=context, agent_type=request.agent_type
        )
    else:
        result = await agent_executor.execute(
            query=request.message, context=context, agent_type=request.agent_type
        )

    return {
        "agent_type": result.agent_type,
        "agent_name": AgentSelector().get_agent_definition(result.agent_type).metadata.name
        if AgentSelector().get_agent_definition(result.agent_type)
        else result.agent_type,
        "response": result.response,
        "sources": result.sources,
    }


@router.post("/generate-summary")
async def generate_summary(request: SummaryRequest):
    """
    生成多Agent总结 - 用于分步请求后汇总
    """
    logger.info(
        f"[GenerateSummary] query: {request.query[:30]}..., agents: {len(request.agent_results)}"
    )

    all_responses = "\n\n".join(
        [
            f"【{r.get('agent_name', r.get('agent_type', 'Agent'))}】: {r.get('response', '')}"
            for r in request.agent_results
        ]
    )

    summary_prompt = f"""请综合以下各位专家的意见，给出一个全面、综合的建议：

{all_responses}

用户问题：{request.query}

请给出一个综合性的回答，总结各位专家的观点，并给出最终建议。"""

    try:
        from app.services.llm_client import get_llm_client

        summary = await get_llm_client().chat_with_system(
            system_prompt="你是一位资深的健康顾问，需要综合各位专家的意见给出最佳建议。",
            user_message=summary_prompt,
            temperature=0.7,
            max_tokens=3000,
        )
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        summary = "感谢各位专家的建议。请根据个人情况选择最适合的方案。"

    return {"summary": summary}
