"""Integration-only tables: sensitive content is encrypted before persistence."""
from sqlalchemy import Column, String, Integer, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ConsultationSession(Base):
    __tablename__ = "integration_consultation_sessions"
    id = Column(String(40), primary_key=True)
    client_id = Column(String(80), nullable=False, index=True)
    subject = Column(String(128), nullable=False, index=True)
    title_cipher = Column(Text, nullable=False)
    created_at = Column(String(32), nullable=False)
    updated_at = Column(String(32), nullable=False)
    deleted_at = Column(String(32))


class ConsultationRun(Base):
    __tablename__ = "integration_consultation_runs"
    __table_args__ = (UniqueConstraint("session_id", "idempotency_key", name="uq_sm_run_idempotency"),)
    id = Column(String(40), primary_key=True)
    session_id = Column(String(40), nullable=False, index=True)
    client_id = Column(String(80), nullable=False, index=True)
    subject = Column(String(128), nullable=False, index=True)
    key_id = Column(String(80), nullable=False)
    active_session = Column(String(40), unique=True)
    idempotency_key = Column(String(80), nullable=False)
    request_hash = Column(String(64), nullable=False)
    request_cipher = Column(Text, nullable=False)
    result_cipher = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    last_seq = Column(Integer, nullable=False, default=0)
    error_code = Column(String(60))
    created_at = Column(String(32), nullable=False)
    updated_at = Column(String(32), nullable=False)


class ConsultationEvent(Base):
    __tablename__ = "integration_consultation_events"
    run_id = Column(String(40), primary_key=True)
    seq = Column(Integer, primary_key=True)
    payload_cipher = Column(Text, nullable=False)
