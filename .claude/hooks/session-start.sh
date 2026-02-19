#!/bin/bash
set -euo pipefail

# Only run in Claude Code remote (web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Set PYTHONPATH so modules resolve from repo root
echo 'export PYTHONPATH="$CLAUDE_PROJECT_DIR"' >> "$CLAUDE_ENV_FILE"

# Install Python dependencies
pip install --quiet -r "$CLAUDE_PROJECT_DIR/requirements.txt"
