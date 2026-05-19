"""
初始化用户数据
运行: python init_users.py
"""

import sys

sys.path.insert(0, ".")

import uuid
from datetime import datetime

from app.models.models import User, Role, Permission
from app.utils.database import SessionLocal


def hash_password(password: str) -> str:
    import hashlib

    return hashlib.sha256(password.encode()).hexdigest()


def init_data():
    session = SessionLocal()
    try:
        # 检查是否已有用户
        existing = session.query(User).first()
        if existing:
            print("[INFO] Users already exist, skipping...")
            return

        # 创建用户
        users = [
            User(
                id=str(uuid.uuid4()),
                username="admin",
                password_hash=hash_password("admin123"),
                name="系统管理员",
                phone="13800000000",
                email="admin@wellhealth.com",
                role="admin",
                login_type="password",
                is_active=True,
            ),
            User(
                id=str(uuid.uuid4()),
                username="doctor",
                password_hash=hash_password("doctor123"),
                name="张医生",
                phone="13800000001",
                email="doctor@wellhealth.com",
                role="doctor",
                login_type="password",
                is_active=True,
            ),
            User(
                id=str(uuid.uuid4()),
                username="patient1",
                password_hash=hash_password("patient123"),
                name="李患者",
                phone="13800000002",
                email="patient1@wellhealth.com",
                role="patient",
                login_type="password",
                is_active=True,
            ),
            User(
                id=str(uuid.uuid4()),
                username="family1",
                password_hash=hash_password("family123"),
                name="王家属",
                phone="13800000003",
                email="family1@wellhealth.com",
                role="family",
                login_type="password",
                is_active=True,
            ),
        ]

        for user in users:
            session.add(user)

        # 创建角色
        roles = [
            Role(
                id=str(uuid.uuid4()),
                name="管理员",
                code="admin",
                description="系统管理员",
                is_system=True,
            ),
            Role(
                id=str(uuid.uuid4()), name="医生", code="doctor", description="医生", is_system=True
            ),
            Role(
                id=str(uuid.uuid4()),
                name="患者",
                code="patient",
                description="患者",
                is_system=True,
            ),
            Role(
                id=str(uuid.uuid4()), name="家属", code="family", description="家属", is_system=True
            ),
        ]
        for role in roles:
            session.add(role)

        # 创建权限
        permissions = [
            # 患者权限
            Permission(
                id=str(uuid.uuid4()),
                name="查看自己档案",
                code="patient:read:self",
                resource="patient",
                action="read",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="管理自己健康数据",
                code="health:read:self",
                resource="health",
                action="read",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="记录健康数据",
                code="health:write:self",
                resource="health",
                action="write",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="查看自己预测",
                code="prediction:read:self",
                resource="prediction",
                action="read",
            ),
            # 家属权限
            Permission(
                id=str(uuid.uuid4()),
                name="查看家属档案",
                code="patient:read:family",
                resource="patient",
                action="read",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="查看家属健康",
                code="health:read:family",
                resource="health",
                action="read",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="查看亲情账号",
                code="family:read",
                resource="family",
                action="read",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="管理亲情账号",
                code="family:write",
                resource="family",
                action="write",
            ),
            # 医生权限
            Permission(
                id=str(uuid.uuid4()),
                name="查看患者",
                code="patient:read",
                resource="patient",
                action="read",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="管理患者",
                code="patient:write",
                resource="patient",
                action="write",
            ),
            # 管理员权限
            Permission(
                id=str(uuid.uuid4()),
                name="删除患者",
                code="patient:delete",
                resource="patient",
                action="delete",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="删除家属",
                code="family:delete",
                resource="family",
                action="delete",
            ),
            Permission(
                id=str(uuid.uuid4()),
                name="所有管理权限",
                code="admin:all",
                resource="admin",
                action="all",
            ),
        ]
        for perm in permissions:
            session.add(perm)

        session.commit()
        print("[SUCCESS] Initial users and permissions created!")
        print("\n默认登录账号:")
        print("  管理员: admin / admin123")
        print("  医生:   doctor / doctor123")
        print("  患者:   patient1 / patient123")
        print("  家属:   family1 / family123")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_data()
