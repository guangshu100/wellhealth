"""Standalone ASGI entry; no legacy chat/admin routes and no automatic schema changes."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, Query, Request
from fastapi.responses import JSONResponse
from .auth import Principal, RateLimiter, principal
from .errors import IntegrationError
from .repository import Store
from .schemas import CreateRun, CreateSession, AGENTS, DISCLAIMER
from .service import ConsultationService
from .settings import Settings

PREFIX = "/api/v1/integrations/smartmedicine"
logger = logging.getLogger(__name__)


def create_app(settings=None, engine_factory=None):
    settings = settings or Settings.from_env()
    store = None
    if settings.enabled:
        settings.validate()
        store = Store(settings)
    if engine_factory is None:
        from .executor import RealEngine
        engine_factory = RealEngine

    @asynccontextmanager
    async def lifespan(application):
        if store:
            # The shared legacy providers log query/key fragments; suppress them only
            # in this standalone process. Our own errors use sanitized codes.
            logging.getLogger("app.services").setLevel(logging.CRITICAL + 1)
            if not store.ready():
                raise RuntimeError("Integration tables missing; run the explicit init-db command first")
            store.recover_interrupted()
        yield
        if application.state.service:
            await application.state.service.shutdown()
        if store:
            store.engine.dispose()

    app = FastAPI(title="SmartMedicine Consultation Integration", version="1.0.0",
                  docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.state.settings = settings
    app.state.store = store
    app.state.limiter = RateLimiter(settings.rate_limit)
    app.state.service = ConsultationService(settings, store, engine_factory) if store else None

    @app.exception_handler(IntegrationError)
    async def domain_error(request, error):
        return JSONResponse(status_code=error.status, content={"error":{"code":error.code,"message":error.message}})

    @app.exception_handler(Exception)
    async def internal_error(request, error):
        logger.error("Integration request failed (%s)", type(error).__name__)
        return JSONResponse(status_code=503, content={"error":{"code":"SERVICE_UNAVAILABLE","message":"会诊服务暂不可用"}})

    @app.get("/health")
    async def health():
        return {"service":"smartmedicine-consultation", "enabled":settings.control()["mode"] != "disabled"}

    @app.get(PREFIX + "/openapi.json")
    async def openapi(actor: Principal = Depends(principal)):
        return app.openapi()

    @app.get(PREFIX + "/capabilities")
    async def capabilities(actor: Principal = Depends(principal)):
        return {"schema_version":1, "enabled":settings.control()["mode"] == "enabled",
                "mode":settings.control()["mode"], "agents":[{"type":k,"name":v} for k,v in AGENTS.items()],
                "max_agents":3, "max_rounds":2, "max_message_length":2000,
                "transport":"poll", "disclaimer":DISCLAIMER}

    @app.post(PREFIX + "/sessions")
    async def create_session(body: CreateSession, actor: Principal = Depends(principal)):
        app.state.service.require_creation()
        return store.create_session(actor, body.title)

    @app.get(PREFIX + "/sessions")
    async def sessions(actor: Principal = Depends(principal), offset: int = Query(0, ge=0, le=10000),
                       limit: int = Query(30, ge=1, le=50)):
        return store.sessions(actor, offset, limit)

    @app.get(PREFIX + "/sessions/{sid}")
    async def session(sid: str, actor: Principal = Depends(principal)):
        return store.session(actor, sid)

    @app.delete(PREFIX + "/sessions/{sid}")
    async def delete_session(sid: str, actor: Principal = Depends(principal)):
        return app.state.service.delete(actor, sid)

    @app.post(PREFIX + "/sessions/{sid}/runs", status_code=202)
    async def create_run(sid: str, body: CreateRun, actor: Principal = Depends(principal),
                         idempotency_key: str = Header(default="", alias="Idempotency-Key")):
        return app.state.service.submit(actor, sid, idempotency_key, body.model_dump())

    @app.get(PREFIX + "/runs/{rid}")
    async def run(rid: str, actor: Principal = Depends(principal), after_seq: int = Query(0, ge=0)):
        return store.run(actor, rid, after_seq)

    @app.post(PREFIX + "/runs/{rid}/cancel")
    async def cancel(rid: str, actor: Principal = Depends(principal)):
        return app.state.service.cancel(actor, rid)

    return app


app = create_app()
