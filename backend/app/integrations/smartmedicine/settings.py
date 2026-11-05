"""Dedicated environment configuration. Never reads or changes the legacy .env."""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    enabled: bool = False
    database_url: str = ""
    data_key: str = ""
    api_key_hashes: dict[str, str] = field(default_factory=dict)
    client_id: str = "smartmedicine"
    control_file: str = ""
    max_concurrent_runs: int = 2
    max_subject_runs: int = 1
    rate_limit: int = 120
    max_runs_per_hour: int = 12
    expert_timeout: float = 60
    run_timeout: float = 420
    retention_days: int = 7

    @classmethod
    def from_env(cls):
        """Load only this module's prefix; absent credentials leave service disabled."""
        prefix = "SM_CONSULT_"
        return cls(
            enabled=os.getenv(prefix + "ENABLED", "false").lower() == "true",
            database_url=os.getenv(prefix + "DATABASE_URL", ""),
            data_key=os.getenv(prefix + "DATA_KEY", ""),
            api_key_hashes=json.loads(os.getenv(prefix + "KEY_HASHES", "{}")),
            client_id=os.getenv(prefix + "CLIENT_ID", "smartmedicine"),
            control_file=os.getenv(prefix + "CONTROL_FILE", ""),
            max_concurrent_runs=int(os.getenv(prefix + "MAX_CONCURRENT_RUNS", "2")),
            expert_timeout=float(os.getenv(prefix + "EXPERT_TIMEOUT", "60")),
            run_timeout=float(os.getenv(prefix + "RUN_TIMEOUT", "420")),
            retention_days=int(os.getenv(prefix + "RETENTION_DAYS", "7")),
        )

    def validate(self):
        if not self.database_url or not self.data_key or not self.api_key_hashes:
            raise ValueError("Integration database, data encryption key and key hashes are required")
        if not 1 <= self.max_concurrent_runs <= 8 or not 1 <= self.retention_days <= 365:
            raise ValueError("Invalid integration resource limits")
        if self.expert_timeout <= 0 or self.run_timeout <= 0:
            raise ValueError("Timeout must be positive")
        if any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
               for value in self.api_key_hashes.values()):
            raise ValueError("API key hashes must be lowercase SHA256 hex strings")
        if int(os.getenv("WEB_CONCURRENCY", "1")) != 1:
            raise ValueError("Demo runner requires exactly one worker")

    def control_document(self):
        """Strict read used by locked operator updates; malformed state is never rewritten."""
        if not self.control_file:
            return {"mode": "enabled", "revoked_key_ids": []}
        path = Path(self.control_file)
        if path.stat().st_size > 65536:
            raise ValueError("Control document too large")
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or data.get("mode") not in {"enabled", "draining", "disabled"}:
            raise ValueError("Invalid control mode")
        revoked = data.get("revoked_key_ids", [])
        if not isinstance(revoked, list) or any(not isinstance(key, str) or not 1 <= len(key) <= 80 for key in revoked):
            raise ValueError("Invalid revoked keys")
        return {"mode": data["mode"], "revoked_key_ids": list(revoked)}

    def control(self):
        """Runtime reads always fail closed, including valid JSON of the wrong shape."""
        try:
            data = self.control_document()
            if not self.enabled:
                data["mode"] = "disabled"
            return data
        except (OSError, ValueError, TypeError):
            return {"mode": "disabled", "revoked_key_ids": []}
