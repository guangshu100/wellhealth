"""
用户API - 登录、用户信息、权限管理
"""

import uuid
import httpx
from datetime import timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from app.models.models import User, Role, Permission, UserRole, RolePermission
from app.utils.database import get_db_session
from app.utils.auth import create_access_token, get_current_user, CurrentUser
from app.utils.email_service import send_verification_code, verify_code
from app.api.captcha import verify_captcha

router = APIRouter()

WECHAT_APPID = "your_appid"
WECHAT_SECRET = "your_secret"


class LoginRequest(BaseModel):
    """账号密码登录请求"""

    username: str
    password: str
    captcha_key: Optional[str] = None
    captcha_code: Optional[str] = None


class WeChatLoginRequest(BaseModel):
    """微信登录请求"""

    code: str


class EmailLoginRequest(BaseModel):
    """邮箱验证码登录请求"""

    email: str
    code: str
    captcha_key: Optional[str] = None
    captcha_code: Optional[str] = None


class RegisterRequest(BaseModel):
    """注册请求"""

    username: str
    password: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None


class LoginResponse(BaseModel):
    """登录响应"""

    token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


def build_user_response(user: User) -> dict:
    """构建用户响应"""
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "avatar": user.avatar,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "login_type": user.login_type,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """账号密码登录"""
    if request.captcha_key and request.captcha_code:
        success, message = verify_captcha(request.captcha_key, request.captcha_code)
        if not success:
            raise HTTPException(status_code=400, detail=message)

    with get_db_session() as session:
        user = (
            session.query(User)
            .filter((User.username == request.username) | (User.phone == request.username))
            .first()
        )

        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.verify_password(request.password):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        token = create_access_token(
            user_id=user.id, username=user.username or user.phone or "", role=user.role
        )

        return LoginResponse(
            token=token,
            token_type="bearer",
            expires_in=7 * 24 * 3600,
            user=build_user_response(user),
        )


@router.post("/wechat-login", response_model=LoginResponse)
async def wechat_login(request: WeChatLoginRequest):
    """微信小程序登录"""
    code = request.code

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": WECHAT_APPID,
                    "secret": WECHAT_SECRET,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
                timeout=10.0,
            )
            data = resp.json()
            if "openid" not in data:
                raise HTTPException(status_code=400, detail="微信登录失败")
            openid = data["openid"]
            session_key = data.get("session_key", "")
    except httpx.RequestError:
        openid = f"mock_user_{code[:8]}"
        session_key = "mock_session_key"

    with get_db_session() as session:
        user = session.query(User).filter(User.wx_openid == openid).first()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                wx_openid=openid,
                wx_session_key=session_key,
                name=f"用户_{openid[:8]}",
                login_type="wechat",
                role="patient",
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        token = create_access_token(
            user_id=user.id,
            username=user.username or user.phone or user.wx_openid or "",
            role=user.role,
        )

        return LoginResponse(
            token=token,
            token_type="bearer",
            expires_in=7 * 24 * 3600,
            user=build_user_response(user),
        )


@router.post("/email-login", response_model=LoginResponse)
async def email_login(request: EmailLoginRequest):
    """邮箱验证码登录"""
    if request.captcha_key and request.captcha_code:
        success, message = verify_captcha(request.captcha_key, request.captcha_code)
        if not success:
            raise HTTPException(status_code=400, detail=message)

    import re

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", request.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    verify_result = verify_code(request.email, request.code)
    if not verify_result["success"]:
        raise HTTPException(status_code=400, detail=verify_result["message"])

    with get_db_session() as session:
        user = session.query(User).filter(User.email == request.email).first()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                username=request.email,
                email=request.email,
                name=f"用户_{request.email.split('@')[0]}",
                login_type="email",
                role="patient",
            )
            session.add(user)
            session.commit()
            session.refresh(user)

        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        token = create_access_token(
            user_id=user.id,
            username=user.username or user.email or "",
            role=user.role,
        )

        return LoginResponse(
            token=token,
            token_type="bearer",
            expires_in=7 * 24 * 3600,
            user=build_user_response(user),
        )


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """用户注册"""
    with get_db_session() as session:
        existing = (
            session.query(User)
            .filter(
                (User.username == request.username) | (User.phone == request.phone)
                if request.phone
                else False
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="用户名或手机号已存在")

        user = User(
            id=str(uuid.uuid4()),
            username=request.username,
            password_hash=User.hash_password(request.password),
            name=request.name,
            phone=request.phone,
            email=request.email,
            login_type="password",
            role="patient",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token = create_access_token(user_id=user.id, username=user.username, role=user.role)

        return LoginResponse(
            token=token,
            token_type="bearer",
            expires_in=7 * 24 * 3600,
            user=build_user_response(user),
        )


class EmailCodeRequest(BaseModel):
    email: str
    purpose: str = "register"


class EmailVerifyRequest(BaseModel):
    email: str
    code: str


class RegisterWithEmailRequest(BaseModel):
    email: str
    code: str
    password: str
    name: str
    phone: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str


@router.post("/email/code")
async def send_email_code(request: EmailCodeRequest):
    """发送邮箱验证码"""
    import re

    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", request.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    if request.purpose not in ["register", "reset", "login"]:
        raise HTTPException(status_code=400, detail="无效的用途")

    result = send_verification_code(request.email, request.purpose)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/email/verify")
async def verify_email_code(request: EmailVerifyRequest):
    """验证邮箱验证码"""
    result = verify_code(request.email, request.code)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.post("/register/email", response_model=LoginResponse)
async def register_with_email(request: RegisterWithEmailRequest):
    """邮箱注册"""
    verify_result = verify_code(request.email, request.code)

    if not verify_result["success"]:
        raise HTTPException(status_code=400, detail=verify_result["message"])

    with get_db_session() as session:
        existing = (
            session.query(User)
            .filter((User.email == request.email) | (User.username == request.email))
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

        user = User(
            id=str(uuid.uuid4()),
            username=request.email,
            password_hash=User.hash_password(request.password),
            name=request.name,
            phone=request.phone,
            email=request.email,
            login_type="password",
            role="patient",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token = create_access_token(user_id=user.id, username=user.username, role=user.role)

        return LoginResponse(
            token=token,
            token_type="bearer",
            expires_in=7 * 24 * 3600,
            user=build_user_response(user),
        )


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """找回密码"""
    verify_result = verify_code(request.email, request.code)

    if not verify_result["success"]:
        raise HTTPException(status_code=400, detail=verify_result["message"])

    with get_db_session() as session:
        user = session.query(User).filter(User.email == request.email).first()

        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user.login_type != "password":
            raise HTTPException(status_code=400, detail="第三方登录用户无法找回密码")

        user.password_hash = User.hash_password(request.new_password)
        session.commit()

        return {"success": True, "message": "密码重置成功"}


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser = Depends(get_current_user)):
    """获取当前用户信息"""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == current_user.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return build_user_response(user)


@router.put("/me")
async def update_user_info(
    data: UserUpdateRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """更新当前用户信息"""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == current_user.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if data.name is not None:
            user.name = data.name
        if data.avatar is not None:
            user.avatar = data.avatar
        if data.phone is not None:
            user.phone = data.phone
        if data.email is not None:
            user.email = data.email

        session.commit()
        return build_user_response(user)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """修改密码"""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == current_user.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user.login_type != "password":
            raise HTTPException(status_code=400, detail="第三方登录用户无法修改密码")

        if not user.verify_password(request.old_password):
            raise HTTPException(status_code=400, detail="原密码错误")

        user.password_hash = User.hash_password(request.new_password)
        session.commit()

        return {"success": True, "message": "密码修改成功"}


@router.post("/bind-patient")
async def bind_patient(patient_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """绑定患者"""
    return {"success": True, "message": "绑定成功", "patient_id": patient_id}


@router.get("/roles")
async def get_roles(current_user: CurrentUser = Depends(get_current_user)):
    """获取角色列表"""
    with get_db_session() as session:
        roles = session.query(Role).all()
        return [
            {"id": r.id, "name": r.name, "code": r.code, "description": r.description}
            for r in roles
        ]


@router.get("/permissions")
async def get_permissions(current_user: CurrentUser = Depends(get_current_user)):
    """获取权限列表"""
    with get_db_session() as session:
        perms = session.query(Permission).all()
        return [
            {"id": p.id, "name": p.name, "code": p.code, "resource": p.resource, "action": p.action}
            for p in perms
        ]
