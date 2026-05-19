"""
数据库工具模块
支持同步和异步两种数据库操作模式
"""

import asyncio
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base

from app.config import settings

# 同步引擎（用于所有数据库操作）
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,
    connect_args={"charset": "utf8mb4", "connect_timeout": 10},
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
)

# 同步 Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """初始化数据库（用于启动时验证连接，不自动创建表）"""
    try:
        with engine.connect() as conn:
            pass
        print("[INFO] Database connection verified")
    except Exception as e:
        print(f"[WARN] Database connection failed: {e}")


def create_tables():
    """创建所有数据库表（仅用于开发环境，生产环境应使用 Alembic）"""
    pass


# ============ 数据库会话 ============


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """获取数据库会话（上下文管理器，用于 Service 层 - 同步模式）"""
    import logging
    _logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        _logger.debug("数据库会话开始")
        yield db
        _logger.debug("数据库会话提交")
        db.commit()
    except Exception as e:
        _logger.error(f"数据库会话回滚: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        _logger.debug("数据库会话关闭")
        db.close()


class AsyncGetDB:
    """异步数据库会话类 - 用于兼容旧的 async with 语法"""

    def __init__(self):
        self.session = SessionLocal()

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


def get_db_session_async():
    """获取数据库会话（异步上下文管理器，用于兼容旧的 async with 语法）"""
    return AsyncGetDB()
