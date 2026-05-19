"""
JWT认证模块
"""

import uuid
import jwt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from functools import lru_cache

from app.config import settings

security = HTTPBearer()


class TokenPayload(BaseModel):
    """Token载荷"""

    sub: str
    user_id: str
    username: str
    role: str
    exp: Optional[int] = None


class CurrentUser(BaseModel):
    """当前用户"""

    user_id: str
    username: str
    role: str
    name: str
    permissions: List[str] = []


def create_access_token(
    user_id: str, username: str, role: str, expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": username,
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "type": "access",
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_token(token: str) -> TokenPayload:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """获取当前用户（依赖注入）"""
    token = credentials.credentials
    payload = decode_token(token)

    from app.models.models import User
    from app.utils.database import get_db_session

    with get_db_session() as session:
        user = session.query(User).filter(User.id == payload.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用"
            )

        permissions = get_user_permissions(user.role)

        return CurrentUser(
            user_id=user.id,
            username=user.username or user.phone or user.wx_openid or "",
            role=user.role,
            name=user.name,
            permissions=permissions,
        )


def get_user_permissions(role: str) -> List[str]:
    """获取用户角色权限"""
    role_permissions = {
        "admin": [
            "patient:read",
            "patient:write",
            "patient:delete",
            "family:read",
            "family:write",
            "family:delete",
            "health:read",
            "health:write",
            "prediction:read",
            "prediction:write",
            "recipe:read",
            "recipe:write",
            "chat:read",
            "chat:write",
            "admin:all",
        ],
        "doctor": [
            "patient:read",
            "patient:write",
            "family:read",
            "health:read",
            "health:write",
            "prediction:read",
            "prediction:write",
            "chat:read",
            "chat:write",
        ],
        "patient": [
            "patient:read:self",
            "family:read",
            "health:read:self",
            "health:write:self",
            "prediction:read:self",
            "recipe:read",
            "recipe:write",
            "chat:read",
            "chat:write",
        ],
        "family": [
            "patient:read:family",
            "family:read",
            "family:write",
            "health:read:family",
            "prediction:read:family",
            "chat:read",
            "chat:write",
        ],
    }
    return role_permissions.get(role, [])


def require_permission(permission: str):
    """权限检查装饰器"""

    def dependency(current_user: CurrentUser = Depends(get_current_user)):
        if (
            permission not in current_user.permissions
            and "admin:all" not in current_user.permissions
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有权限")
        return current_user

    return dependency


def require_roles(*roles: str):
    """角色检查装饰器"""

    def dependency(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in roles and current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="角色不匹配")
        return current_user

    return dependency


class OptionalAuth:
    """可选认证 - 有token则解析，无token则返回None"""

    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    ):
        if not credentials:
            return None

        try:
            return await get_current_user(credentials)
        except HTTPException:
            return None
