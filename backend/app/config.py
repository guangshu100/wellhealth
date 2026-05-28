import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "WellHealth"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "wellhealth"
    MYSQL_PASSWORD: str = "wellhealth123"
    MYSQL_DATABASE: str = "wellhealth"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None

    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_MODEL: str = "qwen-plus"

    SILICONFLOW_API_KEY: Optional[str] = None
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "Qwen/Qwen2-7B-Instruct"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 120

    SECRET_KEY: str = "wellhealth-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24 * 7

    EMAIL_ENABLED: bool = False
    EMAIL_HOST: str = "smtp.qq.com"
    EMAIL_PORT: int = 465
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8443",
        "http://localhost:1420",
        "https://localhost:1420",
    ]

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

print(f"[DEBUG] Settings loaded - LLM_PROVIDER: {settings.LLM_PROVIDER}")
print(
    f"[DEBUG] Settings loaded - SILICONFLOW_API_KEY: {settings.SILICONFLOW_API_KEY[:10] if settings.SILICONFLOW_API_KEY else 'None'}..."
)
print(f"[DEBUG] Settings loaded - SILICONFLOW_MODEL: {settings.SILICONFLOW_MODEL}")
