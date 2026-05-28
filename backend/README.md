# WellHealth Backend

康伴(WellHealth)慢病管理AI平台后端服务


没有 `requirements.txt`，项目用的是 `pyproject.toml`。用 `pip install -e .` 或直接根据 `pyproject.toml` 安装依赖：
项目使用 Poetry 管理依赖。在已激活的 venv 中执行：

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

pip install poetry

poetry install
```

或者如果你不想用 Poetry，直接用 pip 安装核心依赖：

```powershell
pip install fastapi uvicorn sqlalchemy pymysql pydantic pydantic-settings python-jose passlib python-multipart redis langchain langchain-community langgraph neo4j qdrant-client httpx aiohttp celery python-dotenv alembic
```

安装完成后就可以 `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` 启动了。