#!/usr/bin/env bash
# Replace the existing 18100 backend, preserving the previous container for rollback.
set -Eeuo pipefail
umask 077
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_DIR=${WH_REPO:-$(cd -- "$SCRIPT_DIR/../.." && pwd)}
CONFIG_DIR=${SM_CONFIG_DIR:-/etc/wellhealth-smartmedicine}
STATE_DIR=${SM_STATE_DIR:-/data/wellhealth-smartmedicine}
PYTHON_BIN=${PYTHON_BIN:-python3}
CONTAINER=wellhealth-backend
BASE="$REPO_DIR/deploy/docker-compose.yml"
OVERLAY="$SCRIPT_DIR/docker-compose.replace.yml"
PROJECT=wellhealth-sm-prepare

say() { printf '%s\n' "$*"; }
fail() { printf 'ERROR: %s\n' "$*" >&2; return 1; }
exists() { docker container inspect "$1" >/dev/null 2>&1; }
field() { docker container inspect --format "$2" "$1"; }
private_record() { printf '%s\n' "$2" > "$CONFIG_DIR/$1"; chmod 600 "$CONFIG_DIR/$1"; }

require_config() {
  [[ -f "$BASE" && -f "$REPO_DIR/backend/Dockerfile" ]] || { fail 'Run from a WellHealth repository containing its existing Dockerfile.'; return 1; }
  [[ -f "$CONFIG_DIR/credentials.json" && -f "$CONFIG_DIR/compose.env" && -f "$CONFIG_DIR/consultation.env" ]] || {
    fail 'Missing configuration. Run: bash deploy/smartmedicine/run.sh prepare'; return 1;
  }
  if [[ -f "$CONFIG_DIR/active-project" ]]; then PROJECT=$(cat "$CONFIG_DIR/active-project"); fi
  [[ "$PROJECT" =~ ^[a-z0-9][a-z0-9_-]*$ ]] || { fail 'Invalid stored Compose project.'; return 1; }
}

dc() {
  local -a files=()
  # Preserve the original deployment's middleware variable overrides.
  if [[ -f "$REPO_DIR/deploy/.env" ]]; then files+=(--env-file "$REPO_DIR/deploy/.env"); fi
  files+=(--env-file "$CONFIG_DIR/compose.env")
  BACKEND_PORT="127.0.0.1:18100" SM_CONSULT_CONFIG_DIR="$CONFIG_DIR" \
    docker compose "${files[@]}" --project-name "$PROJECT" -f "$BASE" -f "$OVERLAY" "$@"
}

prepare() {
  "$PYTHON_BIN" "$SCRIPT_DIR/prepare_config.py" prepare --config-dir "$CONFIG_DIR" --state-dir "$STATE_DIR"
  say "Generated Java YAML: $CONFIG_DIR/application-wellhealth.yml"
  say 'Copy/merge that private file into the existing SmartMedicine JAR configuration.'
}

verify() {
  "$PYTHON_BIN" "$SCRIPT_DIR/prepare_config.py" verify --config-dir "$CONFIG_DIR"
}

restore_previous() {
  local backup was_running previous_project stamp
  [[ -f "$CONFIG_DIR/rollback-container.name" ]] || { fail 'No rollback record. Do not delete containers manually.'; return 1; }
  backup=$(cat "$CONFIG_DIR/rollback-container.name")
  [[ "$backup" =~ ^wellhealth-backend-before-sm-[A-Za-z0-9-]+$ ]] || { fail 'Invalid backup container name.'; return 1; }
  exists "$backup" || { fail 'Recorded backup container is missing.'; return 1; }
  was_running=$(cat "$CONFIG_DIR/rollback-was-running")
  if exists "$CONTAINER"; then
    [[ "$(field "$CONTAINER" '{{ index .Config.Labels "com.wellhealth.smartmedicine" }}')" == true ]] || {
      fail 'Current container is not managed by this tool; refusing to replace it during rollback.'; return 1;
    }
    stamp="$(date -u +%Y%m%dT%H%M%SZ)-$RANDOM"
    docker stop "$CONTAINER" >/dev/null
    docker rename "$CONTAINER" "wellhealth-smartmedicine-unused-$stamp"
  fi
  docker rename "$backup" "$CONTAINER"
  if [[ "$was_running" == true ]]; then docker start "$CONTAINER" >/dev/null; fi
  previous_project=$(field "$CONTAINER" '{{ index .Config.Labels "com.docker.compose.project" }}')
  if [[ "$previous_project" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
    private_record active-project "$previous_project"
  else
    private_record active-project wellhealth-sm-prepare
  fi
  say 'Previous container restored. Data and credentials were not deleted or rotated.'
  say 'If the restored service is the legacy platform, disable the new feature in the JAR.'
}

deploy() {
  require_config
  say 'Building with the existing backend/Dockerfile; no replacement Dockerfile is used.'
  dc build backend
  # Validate database access/schema BEFORE stopping the old application.
  dc run --rm --no-deps backend python -m app.integrations.smartmedicine.cli init-db
  local stamp backup was_running had_previous=false
  stamp="$(date -u +%Y%m%dT%H%M%SZ)-$RANDOM"
  backup="wellhealth-backend-before-sm-$stamp"
  if exists "$CONTAINER"; then
    had_previous=true
    was_running=$(field "$CONTAINER" '{{.State.Running}}')
    private_record rollback-container.name "$backup"
    private_record rollback-was-running "$was_running"
    say "Replacing $CONTAINER on port 18100. Existing legacy APIs will no longer be served."
    if [[ "$was_running" == true ]]; then docker stop "$CONTAINER" >/dev/null; fi
    if ! docker rename "$CONTAINER" "$backup"; then
      if [[ "$was_running" == true ]]; then docker start "$CONTAINER" >/dev/null; fi
      fail 'Could not retain the old container; deployment aborted.'; return 1
    fi
  fi
  # Renaming alone does not change Compose labels. A NEW project per release prevents
  # Compose from discovering/recreating the preserved backup via its original labels.
  PROJECT="wellhealth-sm-${stamp,,}"
  local started=false
  if dc run --rm --no-deps backend python -m app.integrations.smartmedicine.cli set-mode enabled; then
    if dc up -d --no-deps backend; then started=true; fi
  fi
  if [[ "$started" == true ]]; then
    local attempt
    for attempt in $(seq 1 30); do
      if verify >/dev/null 2>&1; then
        private_record active-project "$PROJECT"
        say 'Deployment verified: wellhealth-backend, host 127.0.0.1:18100, dedicated consultation entry.'
        if [[ "$had_previous" == true ]]; then say "Previous container retained: $backup"; fi
        say "Java YAML: $CONFIG_DIR/application-wellhealth.yml"
        return 0
      fi
      sleep 2
    done
  fi
  say 'New endpoint did not pass authenticated verification. Restoring the previous container.' >&2
  if [[ "$had_previous" == true ]]; then restore_previous; fi
  fail 'Deployment failed; inspect the service logs without exposing credentials.'
}

usage() {
  cat <<'EOF'
Usage: bash deploy/smartmedicine/run.sh COMMAND
  prepare    Generate private keys and ready-to-use Java YAML once; preserve edits.
  build      Build with the repository's existing backend/Dockerfile.
  deploy     Build, initialize, replace existing 18100 backend, verify, auto-restore on failure.
  verify     Verify the new authenticated API, not merely /health.
  status     Show the active container and runtime switch (without credentials).
  drain      Stop accepting new consultations; existing work may finish.
  disable    Reject new requests and request active work to stop at checkpoints.
  stop       Stop only wellhealth-backend (no deletion).
  rollback   Retain the new container and restore the previous one.
Overrides: WH_REPO, SM_CONFIG_DIR, SM_STATE_DIR, PYTHON_BIN.
EOF
}

case "${1:-help}" in
  prepare) prepare ;;
  build) require_config; dc build backend ;;
  deploy) deploy ;;
  verify) require_config; verify ;;
  status)
    require_config
    docker ps -a --filter "name=^/${CONTAINER}$"
    docker exec "$CONTAINER" python -m app.integrations.smartmedicine.cli status
    ;;
  drain|disable)
    require_config
    mode=draining; [[ "$1" == disable ]] && mode=disabled
    docker exec "$CONTAINER" python -m app.integrations.smartmedicine.cli set-mode "$mode"
    ;;
  stop) docker stop "$CONTAINER" ;;
  rollback) require_config; restore_previous ;;
  help|-h|--help) usage ;;
  *) usage >&2; exit 2 ;;
esac
