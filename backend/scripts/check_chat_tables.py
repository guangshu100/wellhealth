"""
检查数据库表是否存在，如果不存在则创建
"""

import sys

sys.path.insert(0, ".")

from sqlalchemy import text
from app.utils.database import SessionLocal


def check_and_create_tables():
    db = SessionLocal()
    try:
        # 检查表是否存在
        result = db.execute(text("SHOW TABLES LIKE 'chat_%'"))
        tables = result.fetchall()

        if not tables:
            print("No chat tables found, creating...")

            # 创建 chat_sessions 表
            db.execute(
                text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id VARCHAR(64) PRIMARY KEY,
                    patient_id VARCHAR(64),
                    agent_type VARCHAR(32),
                    title VARCHAR(255),
                    status VARCHAR(32) DEFAULT 'active',
                    message_count INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_patient_id (patient_id),
                    INDEX idx_updated_at (updated_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            )

            # 创建 chat_messages 表
            db.execute(
                text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id VARCHAR(64) PRIMARY KEY,
                    session_id VARCHAR(64) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    content TEXT,
                    agent_type VARCHAR(32),
                    sources TEXT,
                    safety_level VARCHAR(32),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_session_id (session_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            )

            db.commit()
            print("Tables created successfully!")
        else:
            print(f"Found tables: {[dict(row._mapping) for row in tables]}")

        # 查看现有数据
        result = db.execute(text("SELECT * FROM chat_sessions LIMIT 10"))
        sessions = result.fetchall()
        print(f"Current sessions: {len(sessions)}")
        for s in sessions:
            print(dict(s._mapping))

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_and_create_tables()
