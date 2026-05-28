"""Celery Beat 定时任务调度配置"""
from celery.schedules import crontab

beat_schedule = {
    "vital-signs-monitor": {
        "task": "check_vital_signs",
        "schedule": crontab(minute="*/30"),  # 每30分钟
    },
    "medication-adherence-check": {
        "task": "check_medication_adherence",
        "schedule": crontab(hour="8,12,18,22", minute="0"),  # 每日4次
    },
    "data-quality-scan": {
        "task": "scan_data_quality",
        "schedule": crontab(hour="2", minute="0"),  # 每日凌晨2点
    },
}
