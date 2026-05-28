"""Celery应用配置"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "wellhealth",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_max_tasks_per_child=1000,
)

# 导入定时调度配置
from app.tasks.schedules import beat_schedule  # noqa: E402

celery_app.conf.beat_schedule = beat_schedule

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
