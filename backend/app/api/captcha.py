"""
图形验证码API - 类似SmartMedicine项目
"""

import uuid
import random
import io
import base64
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

CHARS = "23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ"
CAPTCHA_EXPIRE_SECONDS = 300

captcha_cache = {}


class CaptchaResult(BaseModel):
    captchaKey: str
    captchaImage: str


def generate_random_code(length: int = 4) -> str:
    """生成随机验证码"""
    return "".join(random.choices(CHARS, k=length))


def get_rand_color(fc: int, bc: int) -> tuple:
    """生成随机颜色"""
    if fc > 255:
        fc = 255
    if bc > 255:
        bc = 255
    r = fc + random.randint(0, bc - fc)
    g = fc + random.randint(0, bc - fc)
    b = fc + random.randint(0, bc - fc)
    return (r, g, b)


def create_captcha_image(code: str) -> str:
    """创建验证码图片"""
    from PIL import Image, ImageDraw, ImageFont

    width, height = 120, 40
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(image)

    for _ in range(10):
        x = random.randint(0, width)
        y = random.randint(0, height)
        w = random.randint(0, 12)
        h = random.randint(0, 12)
        draw.ellipse([x, y, x + w, y + h], fill=get_rand_color(160, 200))

    for i, char in enumerate(code):
        color = get_rand_color(20, 110)
        draw.text((20 + i * 22, 10), char, fill=color, font=font)

    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([x1, y1, x2, y2], fill=get_rand_color(200, 250), width=1)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


@router.get("/captcha", response_model=CaptchaResult)
async def get_captcha():
    """获取图形验证码"""
    code = generate_random_code(4)
    captcha_key = uuid.uuid4().hex

    captcha_image = create_captcha_image(code)

    captcha_cache[captcha_key] = {"code": code, "created_at": datetime.utcnow()}

    return CaptchaResult(captchaKey=captcha_key, captchaImage=captcha_image)


def verify_captcha(captcha_key: str, captcha_code: str) -> tuple:
    """验证验证码 - 返回 (success, message)"""
    if not captcha_key or not captcha_code:
        return False, "请输入验证码"

    captcha = captcha_cache.get(captcha_key)
    if not captcha:
        return False, "验证码已失效"

    if (datetime.utcnow() - captcha["created_at"]).total_seconds() > CAPTCHA_EXPIRE_SECONDS:
        del captcha_cache[captcha_key]
        return False, "验证码已过期"

    if captcha["code"].lower() != captcha_code.lower():
        return False, "验证码错误"

    del captcha_cache[captcha_key]
    return True, ""
