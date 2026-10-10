#!/usr/bin/env bash
# AISOD 3A Harness — profile bootstrap.
#
# AISOD 3A is NOT a standalone script. It is Hermes Agent itself, branded and
# wired per the AISOD 3A Charter (Founder's Directive IV). This script creates
# the `aisod3a` Hermes profile and installs the Charter identity (SOUL.md).
#
# The profile is cloned from the `default` profile so it keeps 100% of Hermes's
# capabilities — all tools (file, terminal, web, browser, code_execution,
# vision, delegation, cronjob, kanban, memory, skills), all surfaces (CLI, TUI,
# desktop app, dashboard, messaging gateway), all providers. AISOD 3A is a
# focus layer ON Hermes, never a replacement.
#
# Usage:
#   bash setup.sh            # create the profile + install identity
#   hermes -p aisod3a chat   # run it
#
set -euo pipefail

PROFILE_NAME="aisod3a"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/AppData/Local/hermes}"

if ! command -v hermes >/dev/null 2>&1; then
  echo "ERROR: 'hermes' not found on PATH. Install Hermes Agent first." >&2
  exit 1
fi

if hermes profile list 2>/dev/null | grep -q "$PROFILE_NAME"; then
  echo "Profile '$PROFILE_NAME' already exists — updating identity only."
else
  echo "Creating Hermes profile '$PROFILE_NAME' (cloned from default)..."
  hermes profile create "$PROFILE_NAME" --clone \
    --description "AISOD 3A — AI Automation Agent (Founder's Directive IV). Hermes full-capability profile branded and wired per the AISOD 3A Charter."
fi

DEST="$HERMES_HOME/profiles/$PROFILE_NAME/SOUL.md"
mkdir -p "$(dirname "$DEST")"
cp "$SCRIPT_DIR/profile/SOUL.md" "$DEST"
echo "Installed Charter identity -> $DEST"

cat <<'EOF'

Done. Run the AISOD 3A Harness with:

    hermes -p aisod3a chat

Next: pick a working model/provider for the profile:

    hermes -p aisod3a model

EOF
