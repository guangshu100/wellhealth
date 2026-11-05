"""Deployment tooling contract tests; no Docker, database or real model calls."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import base64
import yaml

ROOT = Path(__file__).resolve().parents[1]


class DeploymentConfigTests(unittest.TestCase):
    def module(self):
        source = ROOT / "prepare_config.py"
        self.assertTrue(source.is_file(), "deployment config generator must be delivered")
        spec = importlib.util.spec_from_file_location("deployment_config", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def invoke(self, module, target, *extra):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = module.main(["prepare", "--config-dir", str(target), *extra])
        return code, output.getvalue()

    def test_generator_is_delivered(self):
        self.assertTrue((ROOT / "prepare_config.py").exists(), "missing config generator")

    def test_generated_credentials_match_python_and_inline_java_yaml(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "config"
            code, text = self.invoke(module, target)
            self.assertEqual(code, 0, text)
            credentials = json.loads((target / "credentials.json").read_text())
            self.assertGreaterEqual(len(credentials["api_key"]), 32)
            self.assertEqual(len(base64.urlsafe_b64decode(credentials["data_key"])), 32)
            self.assertNotEqual(credentials["api_key"], credentials["subject_secret"])
            env = (target / "consultation.env").read_text()
            digest = hashlib.sha256(credentials["api_key"].encode()).hexdigest()
            self.assertIn(digest, env)
            self.assertNotIn(credentials["api_key"], env)
            props = yaml.safe_load((target / "application-wellhealth.yml").read_text())["wellhealth"]["consultation"]
            self.assertEqual(props["api-key"], credentials["api_key"])
            self.assertEqual(props["subject-secret"], credentials["subject_secret"])
            self.assertEqual(props["base-url"], "http://127.0.0.1:18100")
            self.assertTrue(props["allow-insecure-local"])
            self.assertNotIn(credentials["api_key"], text)
            self.assertNotIn(credentials["data_key"], text)
            self.assertNotIn(credentials["subject_secret"], text)

    def test_prepare_is_idempotent_and_never_rotates_keys(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "config"
            self.assertEqual(self.invoke(module, target)[0], 0)
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            self.assertEqual(self.invoke(module, target)[0], 0)
            self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_operator_edits_are_not_overwritten(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "config"
            self.assertEqual(self.invoke(module, target)[0], 0)
            p = target / "application-wellhealth.yml"
            p.write_text("operator-edited: true\n")
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            code, text = self.invoke(module, target)
            self.assertNotEqual(code, 0)
            self.assertIn("refus", text.lower())
            self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})

    def test_partial_provisioning_without_credentials_is_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            (target / "consultation.env").write_text("preserve-me")
            self.assertNotEqual(self.invoke(module, target)[0], 0)
            self.assertFalse((target / "credentials.json").exists())
            self.assertEqual((target / "consultation.env").read_text(), "preserve-me")

    def test_corrupt_credentials_do_not_get_replaced(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            (target / "credentials.json").write_text('{"api_key":"incomplete"}')
            before = (target / "credentials.json").read_bytes()
            self.assertNotEqual(self.invoke(module, target)[0], 0)
            self.assertEqual(before, (target / "credentials.json").read_bytes())

    def test_remote_plaintext_url_is_rejected_before_writes(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "config"
            code, _ = self.invoke(module, target, "--base-url", "http://10.0.0.5:18100")
            self.assertNotEqual(code, 0)
            self.assertFalse((target / "credentials.json").exists())

    def test_verify_uses_key_header_and_does_not_print_secrets(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "config"
            self.assertEqual(self.invoke(module, target)[0], 0)
            key = json.loads((target / "credentials.json").read_text())["api_key"]
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def read(self, *args): return b'{"enabled":true,"schema_version":1,"max_rounds":2,"transport":"poll"}'
            out = io.StringIO()
            with patch.object(module.urllib.request, "urlopen", return_value=Response()) as urlopen, contextlib.redirect_stdout(out):
                self.assertEqual(module.main(["verify", "--config-dir", str(target)]), 0)
                request = urlopen.call_args.args[0]
                self.assertEqual(request.get_header("X-api-key"), key)
                self.assertIn("/api/v1/integrations/smartmedicine/capabilities", request.full_url)
            self.assertNotIn(key, out.getvalue())

    def test_verify_rejects_legacy_health_style_response(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "config"
            self.assertEqual(self.invoke(module, target)[0], 0)
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def read(self, *args): return b'{"status":"healthy"}'
            with patch.object(module.urllib.request, "urlopen", return_value=Response()), contextlib.redirect_stderr(io.StringIO()):
                self.assertNotEqual(module.main(["verify", "--config-dir", str(target)]), 0)

    @unittest.skipIf(os.name == "nt", "POSIX mode checks")
    def test_generated_secret_files_are_private(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "config"
            self.assertEqual(self.invoke(module, target)[0], 0)
            for p in target.iterdir():
                self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)


class DeliveryFilesTests(unittest.TestCase):
    def test_overlay_replaces_existing_backend_not_new_container(self):
        path = ROOT / "docker-compose.replace.yml"
        self.assertTrue(path.exists(), "missing replacement overlay")
        service = yaml.safe_load(path.read_text())["services"]
        self.assertEqual(set(service), {"backend"})
        self.assertIn("app.integrations.smartmedicine.app:app", service["backend"]["command"])
        self.assertEqual(service["backend"]["command"][-2:], ["--workers", "1"])
        self.assertNotIn("ports", service["backend"])
        self.assertNotIn("build", service["backend"])
        self.assertEqual(service["backend"]["labels"]["com.wellhealth.smartmedicine"], "true")

    def test_operator_script_and_examples_are_present(self):
        for name in ["run.sh", "README.md", "application-wellhealth.yml.example", "consultation.env.example", ".gitignore"]:
            self.assertTrue((ROOT / name).exists(), name)
        script = (ROOT / "run.sh").read_text()
        self.assertNotIn("docker rm", script)
        self.assertNotIn(" down", script)
        self.assertIn("docker rename", script)
        self.assertIn("rollback", script)


if __name__ == "__main__":
    unittest.main()
