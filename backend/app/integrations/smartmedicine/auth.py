"""API-Key exception is limited to this dedicated service-to-service application."""
import hashlib
import hmac
import re
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from fastapi import Request, Security
from fastapi.security import APIKeyHeader
from .errors import IntegrationError

key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class Principal:
    client_id: str
    subject: str
    key_id: str


class RateLimiter:
    """Bounded single-process guard; network-level limits are also required."""
    def __init__(self, limit=120, buckets=4096):
        self.limit = limit
        self.buckets = buckets
        self.entries = OrderedDict()

    def check(self, identity):
        now = time.monotonic()
        queue = self.entries.setdefault(identity, deque())
        self.entries.move_to_end(identity)
        while queue and queue[0] < now - 60:
            queue.popleft()
        if len(queue) >= self.limit:
            raise IntegrationError(429, "RATE_LIMITED", "请求过于频繁，请稍后重试")
        queue.append(now)
        if len(self.entries) > self.buckets:
            self.entries.popitem(last=False)


async def principal(request: Request, key: str | None = Security(key_header)) -> Principal:
    settings = request.app.state.settings
    control = settings.control()
    if control["mode"] == "disabled" or request.app.state.store is None:
        raise IntegrationError(503, "INTEGRATION_DISABLED", "多 Agent 会诊服务暂未启用")
    if not key or not 24 <= len(key) <= 256:
        raise IntegrationError(401, "INVALID_SERVICE_KEY", "服务认证失败")
    supplied = hashlib.sha256(key.encode()).hexdigest()
    key_id = next((name for name, digest in settings.api_key_hashes.items()
                   if hmac.compare_digest(supplied, digest)), None)
    if key_id is None or key_id in control.get("revoked_key_ids", []):
        raise IntegrationError(401, "INVALID_SERVICE_KEY", "服务认证失败")
    subject = request.headers.get("X-External-Subject", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", subject):
        raise IntegrationError(400, "INVALID_SUBJECT", "缺少可信用户标识")
    request.app.state.limiter.check((settings.client_id, subject))
    return Principal(settings.client_id, subject, key_id)
