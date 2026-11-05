"""Execute the Bash release workflow against a file-backed fake Docker CLI only."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = os.environ.get("SM_TEST_BASH") or (shutil.which("bash") if os.name != "nt" else None)

FAKE_DOCKER = r'''#!/usr/bin/env bash
set -eu
printf '%s\n' "$*" >> "$FAKE_ROOT/commands.log"
printf '%s\n' "${BACKEND_PORT:-unset}" > "$FAKE_ROOT/port-source"
if [[ "$1" == container && "$2" == inspect ]]; then
  if [[ "${3:-}" == --format ]]; then format=$4; name=$5; else name=$3; format=; fi
  [[ -f "$FAKE_ROOT/$name.state" ]] || exit 1
  IFS='|' read -r running managed project < "$FAKE_ROOT/$name.state"
  case "$format" in
    *State.Running*) printf '%s\n' "$running" ;;
    *com.wellhealth.smartmedicine*) printf '%s\n' "$managed" ;;
    *com.docker.compose.project*) printf '%s\n' "$project" ;;
    *) printf '{}\n' ;;
  esac
elif [[ "$1" == stop || "$1" == start ]]; then
  name=$2
  IFS='|' read -r running managed project < "$FAKE_ROOT/$name.state"
  running=false; [[ "$1" == start ]] && running=true
  printf '%s|%s|%s\n' "$running" "$managed" "$project" > "$FAKE_ROOT/$name.state"
elif [[ "$1" == rename ]]; then
  [[ ! -e "$FAKE_ROOT/$3.state" ]]
  mv "$FAKE_ROOT/$2.state" "$FAKE_ROOT/$3.state"
elif [[ "$1" == compose ]]; then
  shift
  command= project=
  while (( $# )); do
    case "$1" in
      --project-name) project=$2; shift 2 ;;
      --env-file|-f) shift 2 ;;
      build|run|up) command=$1; shift; break ;;
      *) shift ;;
    esac
  done
  if [[ "$command" == run && "$*" == *init-db* && "${FAKE_FAIL_INIT:-0}" == 1 ]]; then exit 9; fi
  if [[ "$command" == up ]]; then
    printf 'true|true|%s\n' "$project" > "$FAKE_ROOT/wellhealth-backend.state"
    [[ "${FAKE_FAIL_UP:-0}" != 1 ]] || exit 8
  fi
else
  printf 'Unexpected fake Docker invocation\n' >&2; exit 99
fi
'''

FAKE_PYTHON = r'''#!/usr/bin/env bash
if [[ "${2:-}" == verify && "${FAKE_FAIL_VERIFY:-0}" == 1 ]]; then exit 7; fi
exit 0
'''


@unittest.skipUnless(BASH, "Set SM_TEST_BASH to run mocked Bash deployment tests on Windows")
class ReplacementWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"; self.bin.mkdir()
        self.fake = self.root / "docker-state"; self.fake.mkdir()
        self.repo = self.root / "repo"
        (self.repo / "backend").mkdir(parents=True)
        (self.repo / "deploy").mkdir()
        (self.repo / "backend/Dockerfile").write_text("FROM example\n")
        (self.repo / "deploy/docker-compose.yml").write_text("services: {}\n")
        self.config = self.root / "private"; self.config.mkdir()
        for name in ["credentials.json", "compose.env", "consultation.env"]:
            (self.config / name).write_text("fake-test-only\n")
        for name, text in [("docker", FAKE_DOCKER), ("fake-python", FAKE_PYTHON), ("sleep", "#!/usr/bin/env bash\nexit 0\n")]:
            path = self.bin / name
            path.write_bytes(text.encode())
            path.chmod(0o755)
        (self.fake / "wellhealth-backend.state").write_text("true|false|original-project\n")

    def run_command(self, command, **extra):
        env = dict(os.environ, WH_REPO=self.repo.as_posix(), SM_CONFIG_DIR=self.config.as_posix(),
                   PYTHON_BIN=(self.bin / "fake-python").as_posix(), FAKE_ROOT=self.fake.as_posix())
        env.update(extra)
        return subprocess.run([BASH, "-c", 'b="$1"; if command -v cygpath >/dev/null 2>&1; then b=$(cygpath -u "$1"); fi; export PATH="$b:$PATH"; exec bash "$2" "$3"',
                               "test", self.bin.as_posix(), (ROOT / "run.sh").as_posix(), command],
                              env=env, capture_output=True, text=True, encoding="utf-8", timeout=30)

    def test_replace_keeps_name_and_port_then_rollback_restores_old_container(self):
        result = self.run_command("deploy")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        current = (self.fake / "wellhealth-backend.state").read_text()
        self.assertTrue(current.startswith("true|true|wellhealth-sm-"))
        backup = (self.config / "rollback-container.name").read_text().strip()
        self.assertEqual((self.fake / (backup + ".state")).read_text(), "false|false|original-project\n")
        result = self.run_command("rollback")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.fake / "wellhealth-backend.state").read_text(), "true|false|original-project\n")
        self.assertTrue(list(self.fake.glob("wellhealth-smartmedicine-unused-*.state")))
        log = (self.fake / "commands.log").read_text()
        self.assertFalse(any(line.startswith("rm ") for line in log.splitlines()))
        self.assertNotIn(" down", log)

    def test_parent_environment_cannot_change_loopback_binding(self):
        result = self.run_command("deploy", BACKEND_PORT="0.0.0.0:19000")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.fake / "port-source").read_text().strip(), "127.0.0.1:18100")

    def test_database_failure_does_not_stop_old_service(self):
        result = self.run_command("deploy", FAKE_FAIL_INIT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.fake / "wellhealth-backend.state").read_text(), "true|false|original-project\n")
        self.assertNotIn("stop wellhealth-backend", (self.fake / "commands.log").read_text())

    def test_failed_new_container_start_restores_previous_service(self):
        result = self.run_command("deploy", FAKE_FAIL_UP="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Restoring the previous container", result.stderr)
        self.assertEqual((self.fake / "wellhealth-backend.state").read_text(), "true|false|original-project\n")

    def test_failed_authenticated_probe_restores_previous_service(self):
        result = self.run_command("deploy", FAKE_FAIL_VERIFY="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Restoring the previous container", result.stderr)
        self.assertEqual((self.fake / "wellhealth-backend.state").read_text(), "true|false|original-project\n")

    def test_next_release_uses_new_compose_project_to_protect_renamed_backup(self):
        first = self.run_command("deploy")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        project = (self.config / "active-project").read_text()
        second = self.run_command("deploy")
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertNotEqual((self.config / "active-project").read_text(), project)
        self.assertGreaterEqual(len(list(self.fake.glob("wellhealth-backend-before-sm-*.state"))), 2)


if __name__ == "__main__":
    unittest.main()
