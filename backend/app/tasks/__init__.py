"""Celery任务包"""
from app.tasks.celery_app import celery_app
import app.tasks.monitor_tasks  # noqa: F401 - 注册任务

__all__ = ["celery_app"]
