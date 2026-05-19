"""
康伴(WellHealth) - 慢病管理AI平台
主应用入口
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api import (
    patients,
    doctors,
    chat,
    knowledge,
    evaluation,
    simulation,
    admin,
    users,
    captcha,
    agent_config,
)
from app.api import medication_reminder, report as report_api, prescription, medication_purchase
from app.api import chronic, calorie, cognitive
from app.api import family, recipe, medication_enhanced, health, prediction
from app.utils.database import init_db

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    init_db()

    # 初始化知识库
    from app.services.knowledge_base import knowledge_manager

    await knowledge_manager.initialize()

    yield
    # 关闭时


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="康伴(WellHealth) - 慢病管理AI平台后端服务",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(patients.router, prefix="/api/v1/patients", tags=["患者"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(doctors.router, prefix="/api/v1/doctors", tags=["医生"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["问答"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["评估"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["仿真"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理"])
app.include_router(medication_reminder.router, prefix="/api/v1/patients", tags=["用药提醒"])
app.include_router(report_api.router, prefix="/api/v1/patients", tags=["体检报告"])
app.include_router(prescription.router, prefix="/api/v1/prescriptions", tags=["处方"])
app.include_router(
    medication_purchase.router, prefix="/api/v1/medication-purchases", tags=["购药记录"]
)
app.include_router(chronic.router, prefix="/api/v1/chronic", tags=["慢病管理"])
app.include_router(calorie.router, prefix="/api/v1/calorie", tags=["卡路里跟踪"])
app.include_router(cognitive.router, prefix="/api/v1/cognitive", tags=["认知健康"])

# 新增路由
app.include_router(family.router, tags=["亲情账号"])
app.include_router(recipe.router, tags=["拍照做菜"])
app.include_router(
    medication_enhanced.router, tags=["用药提醒增强"]
)
app.include_router(health.router, tags=["健康数据"])
app.include_router(prediction.router, tags=["健康预测"])
app.include_router(captcha.router, prefix="/api/v1/captcha", tags=["验证码"])
app.include_router(agent_config.router, prefix="/api/v1/admin", tags=["Agent配置"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "康伴(WellHealth) - 慢病管理AI平台",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
