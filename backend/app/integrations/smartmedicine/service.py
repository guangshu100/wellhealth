"""Bounded single-worker runner with durable progress and explicit restart semantics."""
import asyncio
import re
from contextlib import suppress
from .errors import IntegrationError
from .output_policy import display_result
from .repository import TERMINAL
from .schemas import AGENTS


class ConsultationService:
    def __init__(self, settings, store, engine_factory):
        self.settings, self.store, self.engine_factory = settings, store, engine_factory
        self.tasks = {}

    def require_creation(self):
        if self.settings.control()["mode"] != "enabled":
            raise IntegrationError(503, "INTEGRATION_DISABLED", "会诊暂停接收新请求，已有历史仍可查看")

    def submit(self, actor, sid, key, request):
        self.require_creation()
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", key or ""):
            raise IntegrationError(400, "INVALID_IDEMPOTENCY_KEY", "请提供有效的请求标识")
        result, created = self.store.create_run(actor, sid, key, request)
        if created:
            rid = result["run_id"]
            task = asyncio.create_task(self._execute(rid), name="consultation:" + rid)
            self.tasks[rid] = task
            task.add_done_callback(lambda finished, run_id=rid: self.tasks.pop(run_id, None))
        return {"run_id":result["run_id"], "session_id":sid, "status":result["status"], "next_seq":0}

    def cancel(self, actor, rid):
        response = self.store.cancel(actor, rid)
        if response["status"] not in TERMINAL:
            self._cancel_internal(rid, "USER_CANCELLED")
            response["status"] = "cancelled"
        return response

    def delete(self, actor, sid):
        ids = self.store.delete_session(actor, sid)
        for rid in ids:
            self._cancel_internal(rid, "SESSION_DELETED")
        return {"deleted":True}

    def _cancel_internal(self, rid, reason):
        task = self.tasks.get(rid)
        if task:
            task.cancel()
        self.store.finish(rid, "cancelled", reason)

    def _checkpoint(self, rid):
        state = self.store.internal(rid)
        control = self.settings.control()
        if (control["mode"] == "disabled" or state["key_id"] in control.get("revoked_key_ids", [])
                or state["status"] in TERMINAL or state["status"] == "cancelling"):
            raise asyncio.CancelledError()

    async def _watch_control(self, rid):
        while True:
            await asyncio.sleep(0.25)
            try:
                self._checkpoint(rid)
            except asyncio.CancelledError:
                self._cancel_internal(rid, "INTEGRATION_REVOKED")
                return

    async def _execute(self, rid):
        watcher = asyncio.create_task(self._watch_control(rid))
        try:
            await asyncio.wait_for(self._perform(rid), timeout=self.settings.run_timeout)
        except asyncio.CancelledError:
            self.store.finish(rid, "cancelled", "CANCELLED")
        except asyncio.TimeoutError:
            self.store.finish(rid, "failed", "RUN_TIMEOUT")
        except Exception:
            # Never persist provider exception strings: they may contain URLs, credentials or PHI.
            self.store.finish(rid, "failed", "RUN_FAILED")
        finally:
            watcher.cancel()
            with suppress(asyncio.CancelledError):
                await watcher

    async def _perform(self, rid):
        self._checkpoint(rid)
        state = self.store.internal(rid)
        body, sid = state["request"], state["session_id"]
        self.store.append(rid, "run_started")
        self.store.append(rid, "agents_selected", agent_types=body["agent_types"], rounds=body["rounds"])
        engine = self.engine_factory()
        history = self.store.history(sid, rid)
        opinions, previous, failures = [], [], 0
        for round_number in range(1, body["rounds"]+1):
            current = []
            for agent in body["agent_types"]:
                self._checkpoint(rid)
                labels = {"agent_type":agent, "agent_name":AGENTS[agent], "round":round_number}
                self.store.append(rid, "agent_started", **labels)
                try:
                    raw = await asyncio.wait_for(engine.opinion(agent, body["message"], history,
                          body.get("patient_context", {}), list(previous), round_number),
                          timeout=self.settings.expert_timeout)
                    self._checkpoint(rid)
                    approved = display_result(raw)
                    if approved is None:
                        self.store.append(rid, "agent_failed", **labels, error_code="OUTPUT_BLOCKED")
                        failures += 1
                        continue
                    opinion = {**labels, **approved}
                    opinions.append(opinion)
                    current.append(opinion)
                    self.store.append(rid, "agent_completed", **opinion)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    failures += 1
                    self.store.append(rid, "agent_failed", **labels, error_code="EXPERT_UNAVAILABLE")
            previous = current
            self.store.append(rid, "round_completed", round=round_number)
        if not opinions:
            self.store.finish(rid, "failed", "NO_SAFE_EXPERT_RESULT")
            return
        self._checkpoint(rid)
        self.store.append(rid, "summary_started")
        try:
            raw = await asyncio.wait_for(engine.summary(body["message"], opinions),
                                         timeout=self.settings.expert_timeout)
            self._checkpoint(rid)
            summary = display_result(raw)
        except asyncio.CancelledError:
            raise
        except Exception:
            summary = None
        if summary is None:
            self.store.finish(rid, "partial", "SUMMARY_UNAVAILABLE")
            return
        self.store.append(rid, "summary_completed", **summary)
        self.store.finish(rid, "partial" if failures else "completed")

    async def shutdown(self):
        tasks = list(self.tasks.items())
        for rid, task in tasks:
            task.cancel()
            self.store.finish(rid, "interrupted", "PROCESS_STOPPED")
        await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)
