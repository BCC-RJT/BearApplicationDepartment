#!/bin/bash
set -e

# ==============================================================================
# B.A.D. PLAYBOOK SYNC SCRIPT
# ==============================================================================
# MISSION: Keep the local engineering playbook in sync with the organization.
# ==============================================================================

# --- CONFIGURATION ---
PLAYBOOK_DIR="engineering-playbook"
LOG_FILE="BAD/logs/sync_playbook.log"

# --- LOGGING ---
mkdir -p "BAD/logs"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# --- SYNC ---
log "Starting playbook sync..."

if [ ! -d "$PLAYBOOK_DIR" ]; then
    log "Error: Playbook directory '$PLAYBOOK_DIR' not found."
    exit 1
fi

log "Updating submodule..."
git submodule update --remote --merge "$PLAYBOOK_DIR"

log "Sync complete."
