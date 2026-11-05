"""Explicit operator commands. Never changes the legacy database schema or .env."""
import argparse
import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from .settings import Settings
from .repository import Store


def write_control(path, payload):
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(serialized.encode("utf-8")) > 65536:
        raise ValueError("Control document too large; existing state was not modified")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def control_lock(path):
    """Serialize the entire control transaction across threads/processes on Windows/Unix."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(str(target) + ".lock", "a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"0")
            lock.flush()
        deadline = time.monotonic() + 10
        acquired = False
        try:
            while not acquired:
                lock.seek(0)
                try:
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except (OSError, BlockingIOError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Timed out waiting for integration control lock") from None
                    time.sleep(0.05)
            yield
        finally:
            if acquired:
                lock.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def update_control(settings, mutate):
    """Never use the master-enabled override to replace the stored revocation list."""
    if not settings.control_file:
        raise ValueError("SM_CONSULT_CONTROL_FILE is required")
    with control_lock(settings.control_file):
        if Path(settings.control_file).exists():
            control = settings.control_document()
        else:
            control = {"mode": "disabled", "revoked_key_ids": []}
        mutate(control)
        write_control(settings.control_file, control)


def main():
    parser = argparse.ArgumentParser(description="SmartMedicine integration operations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="Explicitly create only the three integration tables")
    mode = sub.add_parser("set-mode", help="Atomically set the runtime kill switch")
    mode.add_argument("mode", choices=["enabled", "draining", "disabled"])
    revoke = sub.add_parser("revoke-key", help="Revoke a public key ID immediately")
    revoke.add_argument("key_id")
    sub.add_parser("status")
    purge = sub.add_parser("purge", help="Permanently delete expired inactive integration sessions")
    purge.add_argument("--confirm", action="store_true", required=True)
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == "status":
        print(json.dumps({"enabled":settings.enabled, "control":settings.control()}, ensure_ascii=False))
        return
    if args.command in {"set-mode", "revoke-key"}:
        if not settings.control_file:
            parser.error("SM_CONSULT_CONTROL_FILE is required")
        def mutate(control):
            if args.command == "set-mode":
                control["mode"] = args.mode
            else:
                if not 1 <= len(args.key_id) <= 80:
                    parser.error("Invalid key ID")
                control["revoked_key_ids"] = sorted(set(control.get("revoked_key_ids", [])) | {args.key_id})
        update_control(settings, mutate)
        print("Integration runtime controls updated")
        return
    settings.validate()
    store = Store(settings)
    try:
        if args.command == "init-db":
            store.create_schema()
            print("Integration schema ready (three dedicated tables)")
        elif args.command == "purge":
            print("Expired integration sessions removed:", store.purge(settings.retention_days))
    finally:
        store.engine.dispose()


if __name__ == "__main__":
    main()
