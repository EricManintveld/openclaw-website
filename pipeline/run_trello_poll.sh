#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/trello_poll.log"
INTERVAL="${TRELLO_POLL_INTERVAL:-600}"

cd "$SCRIPT_DIR/.."

{
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] starting Trello poll"
  python3 "$SCRIPT_DIR/trello_pipeline.py" --once
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] finished Trello poll"
} >> "$LOG_FILE" 2>&1
