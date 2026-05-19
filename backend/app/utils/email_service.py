"""
邮件服务 - 验证码发送
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional

try:
    import yagmail

    YAGMAIL_AVAILABLE = True
except ImportError:
    YAGMAIL_AVAILABLE = False

from app.config import settings

email_code_store = {}
EMAIL_CODE_EXPIRE_MINUTES = 5


def generate_verification_code(length: int = 6) -> str:
    """生成数字验证码"""
    return "".join(random.choices(string.digits, k=length))


def send_verification_email(to_email: str, code: str, purpose: str = "注册") -> bool:
    """发送验证码邮件"""
    try:
        if not settings.EMAIL_ENABLED or not YAGMAIL_AVAILABLE:
            print(f"[MOCK EMAIL] To: {to_email}, Code: {code}, Purpose: {purpose}")
            return True

        yag = yagmail.SMTP(
            user=settings.EMAIL_USERNAME,
            password=settings.EMAIL_PASSWORD,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
        )

        subject = f"康伴健康 - {'注册' if purpose == 'register' else '找回密码'}验证码"
        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">康伴健康</h1>
            </div>
            <div style="padding: 30px; background: #f9f9f9;">
                <p style="font-size: 16px; color: #333;">您好，</p>
                <p style="font-size: 16px; color: #333;">
                    您的{"注册" if purpose == "register" else "找回密码"}验证码为：
                </p>
                <div style="background: #fff; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; border: 2px dashed #667eea;">
                    <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px;">{code}</span>
                </div>
                <p style="font-size: 14px; color: #666;">
                    验证码有效期为 {EMAIL_CODE_EXPIRE_MINUTES} 分钟，请尽快完成验证。<br/>
                    如非本人操作，请忽略此邮件。
                </p>
            </div>
            <div style="background: #333; padding: 20px; text-align: center;">
                <p style="color: #999; font-size: 12px; margin: 0;">
                    © 2024 康伴健康 - 智能慢病管理平台
                </p>
            </div>
        </div>
        """

        yag.send(to=to_email, subject=subject, contents=content)
        return True

    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False


def send_verification_code(email: str, purpose: str = "register") -> dict:
    """发送邮箱验证码"""
    code = generate_verification_code()

    email_code_store[email] = {
        "code": code,
        "purpose": purpose,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=EMAIL_CODE_EXPIRE_MINUTES),
        "verified": False,
    }

    success = send_verification_email(email, code, purpose)

    if success:
        return {"success": True, "message": "验证码已发送", "email": mask_email(email)}
    else:
        return {"success": False, "message": "发送失败，请稍后重试"}


def verify_code(email: str, code: str) -> dict:
    """验证邮箱验证码"""
    record = email_code_store.get(email)

    if not record:
        return {"success": False, "message": "请先获取验证码"}

    if datetime.utcnow() > record["expires_at"]:
        del email_code_store[email]
        return {"success": False, "message": "验证码已过期，请重新获取"}

    if record["verified"]:
        return {"success": False, "message": "验证码已使用"}

    if record["code"] != code:
        return {"success": False, "message": "验证码错误"}

    record["verified"] = True

    return {"success": True, "message": "验证成功"}


def mask_email(email: str) -> str:
    """脱敏邮箱"""
    if "@" not in email:
        return email

    parts = email.split("@")
    username = parts[0]

    if len(username) <= 2:
        masked = username[0] + "*"
    else:
        masked = username[0] + "*" * (len(username) - 2) + username[-1]

    return f"{masked}@{parts[1]}"


def clear_expired_codes():
    """清理过期验证码"""
    now = datetime.utcnow()
    expired = [email for email, record in email_code_store.items() if now > record["expires_at"]]
    for email in expired:
        del email_code_store[email]
