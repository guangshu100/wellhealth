"""Encrypted, integration-only persistence. All public lookups are owner-scoped."""
import hashlib
import hmac
import json
import threading
import uuid
from datetime import datetime, timezone, timedelta

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select, func, delete, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from .errors import IntegrationError
from .models import Base, ConsultationSession as Chat, ConsultationRun as Run, ConsultationEvent as Event

TERMINAL = {"completed", "partial", "failed", "cancelled", "interrupted"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Store:
    def __init__(self, settings):
        self.settings = settings
        self.cipher = Fernet(settings.data_key.encode())
        kwargs = {"pool_pre_ping": True}
        if settings.database_url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in settings.database_url:
                kwargs["poolclass"] = StaticPool
        self.engine = create_engine(settings.database_url, **kwargs)
        self.db = sessionmaker(self.engine, expire_on_commit=False)
        self.lock = threading.RLock()

    def create_schema(self):
        """Explicit provisioning command only; never automatically called by the app."""
        Base.metadata.create_all(self.engine)

    def ready(self):
        names = set(inspect(self.engine).get_table_names())
        return set(Base.metadata.tables).issubset(names)

    def seal(self, value):
        return self.cipher.encrypt(json.dumps(value, ensure_ascii=False).encode()).decode()

    def open(self, value):
        return json.loads(self.cipher.decrypt(value.encode()).decode())

    def _chat(self, db, actor, sid):
        result = db.scalar(select(Chat).where(Chat.id == sid, Chat.client_id == actor.client_id,
                          Chat.subject == actor.subject, Chat.deleted_at.is_(None)))
        if result is None:
            raise IntegrationError(404, "NOT_FOUND", "会话不存在")
        return result

    def _run(self, db, actor, rid):
        result = db.scalar(select(Run).where(Run.id == rid, Run.client_id == actor.client_id,
                                            Run.subject == actor.subject))
        if result is None:
            raise IntegrationError(404, "NOT_FOUND", "会诊任务不存在")
        self._chat(db, actor, result.session_id)
        return result

    def create_session(self, actor, title):
        stamp = now()
        with self.db.begin() as db:
            chat = Chat(id="cs_" + uuid.uuid4().hex, client_id=actor.client_id, subject=actor.subject,
                        title_cipher=self.seal(title.strip() or "新会诊"), created_at=stamp, updated_at=stamp)
            db.add(chat)
        return self._chat_json(chat)

    def _chat_json(self, chat):
        return {"session_id": chat.id, "title": self.open(chat.title_cipher),
                "created_at": chat.created_at, "updated_at": chat.updated_at}

    def sessions(self, actor, offset=0, limit=30):
        with self.db() as db:
            chats = db.scalars(select(Chat).where(Chat.client_id == actor.client_id,
                               Chat.subject == actor.subject, Chat.deleted_at.is_(None))
                               .order_by(Chat.updated_at.desc(), Chat.id.desc()).offset(offset).limit(limit+1)).all()
            return {"sessions": [self._chat_json(c) for c in chats[:limit]],
                    "has_more": len(chats) > limit, "next_offset": offset + min(limit, len(chats))}

    def session(self, actor, sid):
        with self.db() as db:
            chat = self._chat(db, actor, sid)
            runs = db.scalars(select(Run).where(Run.session_id == sid)
                              .order_by(Run.created_at.desc(), Run.id.desc()).limit(50)).all()
            return {**self._chat_json(chat), "runs": [self._run_json(r) for r in reversed(runs)],
                    "active_run_id": next((r.id for r in runs if r.status not in TERMINAL), None)}

    def _run_json(self, run):
        request, result = self.open(run.request_cipher), self.open(run.result_cipher)
        return {"run_id": run.id, "session_id": run.session_id, "status": run.status,
                "message": request["message"], "rounds": request["rounds"],
                "agent_types": request["agent_types"], "opinions": result.get("opinions", []),
                "summary": result.get("summary", ""), "failures": result.get("failures", []), "error_code": run.error_code,
                "last_seq": run.last_seq, "created_at": run.created_at,
                "patient_context": request.get("patient_context", {})}

    def create_run(self, actor, sid, key, body):
        canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hmac.new(self.settings.data_key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
        with self.lock, self.db.begin() as db:
            chat = self._chat(db, actor, sid)
            existing = db.scalar(select(Run).where(Run.session_id == sid, Run.idempotency_key == key))
            if existing:
                if not hmac.compare_digest(existing.request_hash, digest):
                    raise IntegrationError(409, "IDEMPOTENCY_CONFLICT", "同一请求标识不能用于不同内容")
                return self._run_json(existing), False
            if db.scalar(select(Run.id).where(Run.active_session == sid)):
                raise IntegrationError(409, "SESSION_BUSY", "当前会话已有正在执行的会诊")
            active = db.scalar(select(func.count()).select_from(Run).where(Run.active_session.is_not(None)))
            subject_active = db.scalar(select(func.count()).select_from(Run).where(
                Run.active_session.is_not(None), Run.client_id == actor.client_id, Run.subject == actor.subject))
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="milliseconds")
            recent = db.scalar(select(func.count()).select_from(Run).where(
                Run.client_id == actor.client_id, Run.subject == actor.subject, Run.created_at >= cutoff))
            if active >= self.settings.max_concurrent_runs or subject_active >= self.settings.max_subject_runs:
                raise IntegrationError(429, "CAPACITY_EXCEEDED", "会诊繁忙，请等待当前任务结束")
            if recent >= self.settings.max_runs_per_hour:
                raise IntegrationError(429, "RUN_BUDGET_EXCEEDED", "本小时会诊次数已达上限")
            stamp = now()
            run = Run(id="run_" + uuid.uuid4().hex, session_id=sid, client_id=actor.client_id,
                      subject=actor.subject, key_id=actor.key_id, active_session=sid, idempotency_key=key,
                      request_hash=digest, request_cipher=self.seal(body), result_cipher=self.seal({}),
                      status="queued", last_seq=0, created_at=stamp, updated_at=stamp)
            db.add(run)
            chat.updated_at = stamp
            if self.open(chat.title_cipher) == "新会诊":
                chat.title_cipher = self.seal(body["message"][:24])
            try:
                db.flush()
            except IntegrityError:
                raise IntegrationError(409, "SESSION_BUSY", "会话正在处理另一请求") from None
            return self._run_json(run), True

    def run(self, actor, rid, after_seq=0, limit=100):
        with self.db() as db:
            run = self._run(db, actor, rid)
            if after_seq > run.last_seq:
                raise IntegrationError(409, "CURSOR_AHEAD", "事件游标无效，请重新加载会话")
            rows = db.scalars(select(Event).where(Event.run_id == rid, Event.seq > after_seq)
                              .order_by(Event.seq).limit(limit)).all()
            next_seq = rows[-1].seq if rows else after_seq
            return {"run_id": rid, "session_id": run.session_id, "status": run.status,
                    "events": [self.open(e.payload_cipher) for e in rows], "next_seq": next_seq,
                    "has_more": next_seq < run.last_seq, "retry_after_ms": 1500,
                    "error_code": run.error_code}

    def internal(self, rid):
        with self.db() as db:
            run = db.get(Run, rid)
            return {"request": self.open(run.request_cipher), "session_id": run.session_id,
                    "key_id": run.key_id, "status": run.status}

    def history(self, sid, exclude_run):
        with self.db() as db:
            rows = db.scalars(select(Run).where(Run.session_id == sid, Run.id != exclude_run,
                              Run.status.in_(["completed", "partial"]))
                              .order_by(Run.created_at.desc()).limit(5)).all()
            history = []
            for row in reversed(rows):
                request, result = self.open(row.request_cipher), self.open(row.result_cipher)
                if result.get("summary"):
                    history.extend([{"role":"user", "content":request["message"][:1200]},
                                    {"role":"assistant", "content":result["summary"][:1600]}])
            return history

    def append(self, rid, event_type, **fields):
        with self.lock, self.db.begin() as db:
            run = db.get(Run, rid)
            if run.status in TERMINAL:
                return
            run.last_seq += 1
            run.updated_at = now()
            event = {"schema_version":1, "session_id":run.session_id, "run_id":rid,
                     "seq":run.last_seq, "type":event_type, "timestamp":run.updated_at, **fields}
            db.add(Event(run_id=rid, seq=run.last_seq, payload_cipher=self.seal(event)))
            if event_type == "run_started":
                run.status = "running"
            if event_type == "agent_completed":
                result = self.open(run.result_cipher)
                result.setdefault("opinions", []).append(fields)
                run.result_cipher = self.seal(result)
            if event_type == "agent_failed":
                result = self.open(run.result_cipher)
                result.setdefault("failures", []).append(fields)
                run.result_cipher = self.seal(result)
            if event_type == "summary_completed":
                result = self.open(run.result_cipher)
                result["summary"] = fields["content"]
                run.result_cipher = self.seal(result)

    def finish(self, rid, status, code=None):
        with self.lock, self.db.begin() as db:
            run = db.get(Run, rid)
            if run.status in TERMINAL:
                return
            run.last_seq += 1
            event = {"schema_version":1, "session_id":run.session_id, "run_id":rid,
                     "seq":run.last_seq, "type":"run_" + ("completed" if status in {"completed","partial"} else status),
                     "timestamp":now(), "status":status, "error_code":code}
            db.add(Event(run_id=rid, seq=run.last_seq, payload_cipher=self.seal(event)))
            run.status, run.error_code, run.active_session, run.updated_at = status, code, None, now()

    def cancel(self, actor, rid):
        with self.lock, self.db.begin() as db:
            run = self._run(db, actor, rid)
            if run.status not in TERMINAL:
                run.status = "cancelling"
            return {"run_id":rid, "status":run.status}

    def delete_session(self, actor, sid):
        with self.lock, self.db.begin() as db:
            chat = self._chat(db, actor, sid)
            runs = db.scalars(select(Run).where(Run.session_id == sid, Run.active_session.is_not(None))).all()
            for run in runs:
                run.status = "cancelling"
            chat.deleted_at = now()
            return [r.id for r in runs]

    def recover_interrupted(self):
        with self.db() as db:
            ids = db.scalars(select(Run.id).where(Run.active_session.is_not(None))).all()
        for rid in ids:
            self.finish(rid, "interrupted", "PROCESS_RESTARTED")

    def purge(self, days):
        """Explicit retention operation, excludes active tasks and their sessions."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="milliseconds")
        with self.lock, self.db.begin() as db:
            old = db.scalars(select(Chat).where(Chat.updated_at < cutoff,
                ~Chat.id.in_(select(Run.session_id).where(Run.active_session.is_not(None))))).all()
            for chat in old:
                ids = select(Run.id).where(Run.session_id == chat.id)
                db.execute(delete(Event).where(Event.run_id.in_(ids)))
                db.execute(delete(Run).where(Run.session_id == chat.id))
                db.delete(chat)
            return len(old)
