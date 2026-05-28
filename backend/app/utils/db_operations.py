"""
数据库操作工具类
统一的数据库连接管理、异常处理和日志记录
"""
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.utils.database import SessionLocal

logger = logging.getLogger(__name__)


@contextmanager
def get_session():
    """获取数据库会话的上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"数据库会话回滚: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def execute_query(
    sql: str,
    params: Dict[str, Any] = None,
    fetch_one: bool = False,
) -> Optional[Any]:
    """
    执行查询SQL

    Args:
        sql: SQL语句
        params: 查询参数
        fetch_one: 是否只获取第一条记录

    Returns:
        fetch_one=True时返回单条记录的字典，否则返回记录列表
    """
    try:
        with get_session() as db:
            result = db.execute(text(sql), params or {})
            if fetch_one:
                row = result.fetchone()
                return dict(row._mapping) if row else None
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
    except Exception as e:
        logger.error(f"查询执行失败: {e}", exc_info=True)
        return None


def execute_update(
    sql: str,
    params: Dict[str, Any] = None,
) -> bool:
    """
    执行更新SQL（INSERT/UPDATE/DELETE）

    Args:
        sql: SQL语句
        params: 查询参数

    Returns:
        是否执行成功
    """
    try:
        with get_session() as db:
            db.execute(text(sql), params or {})
            return True
    except Exception as e:
        logger.error(f"更新执行失败: {e}", exc_info=True)
        return False


def execute_in_session(
    callback: Callable[[Session], Any],
) -> Any:
    """
    在数据库会话中执行自定义操作，支持同一事务中的多语句操作

    Args:
        callback: 接收 Session 对象的回调函数

    Returns:
        回调函数的返回值，异常时返回 None
    """
    try:
        with get_session() as db:
            return callback(db)
    except Exception as e:
        logger.error(f"会话操作执行失败: {e}", exc_info=True)
        return None
