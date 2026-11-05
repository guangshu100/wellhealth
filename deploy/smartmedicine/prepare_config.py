#!/usr/bin/env python3
"""Provision deployment files once. Standard library only; never prints credentials."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request

FILES = ("consultation.env", "application-wellhealth.yml", "compose.env")


def safe_value(value):
    if not isinstance(value, str) or any(c in value for c in ("\n", "\r", "\0")):
        raise ValueError("Invalid deployment value")
    return value


def validate_url(value):
    safe_value(value)
    url = urllib.parse.urlsplit(value)
    if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
            or url.username or url.password or url.query or url.fragment
            or url.path not in {"", "/"} or url.port != 18100):
        raise ValueError("This deployment requires an HTTP loopback origin on port 18100")
    return value.rstrip("/")


def private_write(path, content):
    if path.is_symlink():
        raise ValueError("Refusing a symlink destination")
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def env_quote(value):
    return "'" + safe_value(value).replace("'", "\\'") + "'"


def load_credentials(path):
    if path.is_symlink():
        raise ValueError("Refusing symlink credentials")
    data = json.loads(path.read_text(encoding="utf-8"))
    names = ("api_key", "data_key", "subject_secret", "namespace", "key_id", "base_url", "state_dir", "database_url")
    if not isinstance(data, dict) or data.get("schema_version") != 1 or any(n not in data for n in names):
        raise ValueError("Credentials are incomplete; refusing replacement")
    for name in names:
        safe_value(data[name])
    if len(data["api_key"]) < 32 or len(data["subject_secret"]) < 32:
        raise ValueError("Invalid credentials; refusing replacement")
    if len(base64.urlsafe_b64decode(data["data_key"].encode("ascii"))) != 32:
        raise ValueError("Invalid data key; refusing replacement")
    validate_url(data["base_url"])
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", data["key_id"]):
        raise ValueError("Invalid key ID")
    return data


def render(data, target):
    digest = hashlib.sha256(data["api_key"].encode()).hexdigest()
    values = {
        "SM_CONSULT_ENABLED": "true",
        "SM_CONSULT_DATABASE_URL": data["database_url"],
        "SM_CONSULT_DATA_KEY": data["data_key"],
        "SM_CONSULT_KEY_HASHES": json.dumps({data["key_id"]: digest}, separators=(",", ":")),
        "SM_CONSULT_CLIENT_ID": "smartmedicine",
        "SM_CONSULT_CONTROL_FILE": "/var/lib/smartmedicine/control.json",
        "SM_CONSULT_MAX_CONCURRENT_RUNS": "1",
        "SM_CONSULT_EXPERT_TIMEOUT": "120",
        "SM_CONSULT_RUN_TIMEOUT": "900",
        "SM_CONSULT_RETENTION_DAYS": "7",
    }
    env = "# Generated deployment secrets. Never commit this file.\n"
    env += "".join(f"{key}={env_quote(value)}\n" for key, value in values.items())
    props = {
        "enabled": "true", "base-url": json.dumps(data["base_url"]),
        "api-key": json.dumps(data["api_key"]),
        "subject-secret": json.dumps(data["subject_secret"]),
        "subject-namespace": json.dumps(data["namespace"]),
        "allow-insecure-local": "true", "connect-timeout-ms": "3000", "request-timeout-ms": "15000",
    }
    java = "# Merge into the JAR's existing YAML, or load as an additional file.\nwellhealth:\n  consultation:\n"
    java += "".join(f"    {key}: {value}\n" for key, value in props.items())
    compose = "# This file is read only by the deployment script.\n"
    compose += f"SM_CONSULT_CONFIG_DIR={env_quote(target.as_posix())}\n"
    compose += f"SM_CONSULT_STATE_DIR={env_quote(data['state_dir'])}\n"
    # The existing base compose uses ${BACKEND_PORT}:18100; keep host access local.
    compose += "BACKEND_PORT='127.0.0.1:18100'\n"
    return {"consultation.env": env, "application-wellhealth.yml": java, "compose.env": compose}


def prepare(args):
    target = Path(args.config_dir).absolute()
    if target.is_symlink():
        raise ValueError("Refusing a symlink configuration directory")
    base_url = validate_url(args.base_url)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", args.namespace):
        raise ValueError("Invalid namespace")
    state_dir = safe_value(args.state_dir)
    database_url = safe_value(args.database_url)
    path = target / "credentials.json"
    if path.exists() or path.is_symlink():
        data = load_credentials(path)
        expected = {"base_url": base_url, "namespace": args.namespace, "state_dir": state_dir, "database_url": database_url}
        if any(data[k] != v for k, v in expected.items()):
            raise ValueError("Refusing to change existing identity/storage configuration")
        fresh = False
    else:
        if any((target / name).exists() or (target / name).is_symlink() for name in FILES):
            raise ValueError("Refusing partial provisioning without credentials.json")
        data = {
            "schema_version": 1, "api_key": secrets.token_hex(32),
            "data_key": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
            "subject_secret": secrets.token_hex(32), "key_id": "smartmedicine-test-v1",
            "base_url": base_url, "namespace": args.namespace,
            "state_dir": state_dir, "database_url": database_url,
        }
        fresh = True
    outputs = render(data, target)
    # Validate all destinations before writing any file; operator changes are preserved.
    for name, content in outputs.items():
        destination = target / name
        if destination.is_symlink():
            raise ValueError("Refusing a symlink output")
        if destination.exists() and destination.read_text(encoding="utf-8") != content:
            raise ValueError(f"Refusing to overwrite operator-edited {name}")
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    if fresh:
        private_write(path, json.dumps(data, indent=2) + "\n")
    for name, content in outputs.items():
        if not (target / name).exists():
            private_write(target / name, content)
    print(f"Deployment configuration ready: {target}")
    print("Keys are preserved. No secret values were printed. No service was started.")
    return 0


def verify(args):
    data = load_credentials(Path(args.config_dir) / "credentials.json")
    request = urllib.request.Request(
        data["base_url"] + "/api/v1/integrations/smartmedicine/capabilities",
        headers={"X-API-Key": data["api_key"], "X-External-Subject": "deployment-probe-0001"},
    )
    try:
        # Do not follow redirects with an authentication header.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        # urlopen is retained as the testable network boundary; redirects are rejected
        # by the explicit handler temporarily installed for this synchronous CLI.
        previous = urllib.request._opener
        urllib.request.install_opener(urllib.request.build_opener(NoRedirect))
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = response.read(1024 * 1024 + 1)
        finally:
            urllib.request._opener = previous
        if len(body) > 1024 * 1024:
            raise ValueError("Service response is too large")
        result = json.loads(body)
        if result.get("schema_version") != 1 or result.get("enabled") is not True or result.get("max_rounds") != 2:
            raise ValueError("The new consultation API is not enabled on port 18100")
        print("Verified: authenticated SmartMedicine consultation API on 127.0.0.1:18100.")
        print("Transport:", result.get("transport", "unknown"))
        return 0
    except urllib.error.HTTPError as error:
        print(f"Service verification failed: HTTP {error.code}; no credentials were printed.", file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        print("Service verification failed: endpoint unavailable or not the enabled consultation API.", file=sys.stderr)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify"))
    parser.add_argument("--config-dir", default="/etc/wellhealth-smartmedicine")
    parser.add_argument("--state-dir", default="/data/wellhealth-smartmedicine")
    parser.add_argument("--base-url", default="http://127.0.0.1:18100")
    parser.add_argument("--namespace", default="smartmedicine-test")
    parser.add_argument("--database-url", default="sqlite:////var/lib/smartmedicine/consultation.db")
    args = parser.parse_args(argv)
    try:
        return prepare(args) if args.command == "prepare" else verify(args)
    except (ValueError, OSError, KeyError, TypeError):
        print("Refusing unsafe/incomplete configuration or overwrite. Preserve existing files and keys; review the private deployment directory.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
