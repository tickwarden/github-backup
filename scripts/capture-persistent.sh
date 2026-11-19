#!/usr/bin/env bash
set -euo pipefail
umask 077
mkdir -p "$RUNNER_TEMP"
if [[ -f "$RUNNER_TEMP/CAPTURE_OK" ]]; then
 echo "Existing successful capture reused; backup not repeated."
 exit 0
fi
python3 -u scripts/run-with-progress.py
touch "$RUNNER_TEMP/CAPTURE_OK"
