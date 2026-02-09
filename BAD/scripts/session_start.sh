#!/bin/bash

# Session Start Script (VM Side)
# Enforces Protocol: BEGINNING_OF_SESSION (PHASE-01)

set -e

# 1. Location Check
# 1. Location Check
# If we are already in a git repo (e.g. set by bot CWD), stay there.
if git rev-parse --show-toplevel > /dev/null 2>&1; then
    PROJECT_ROOT=$(git rev-parse --show-toplevel)
    echo "✅ Using CWD as Root: $PROJECT_ROOT"
else
    # Fallback: Calculate from script location
    SCRIPT_DIR="$(dirname "$(realpath "$0")")"
    PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")" # BAD/scripts -> BAD -> REPO_ROOT (assuming BAD is inside repo)
    
    # VM Fix: Check if we are in ~/BAD and repo is ~/BearApplicationDepartment
    if [ ! -d "$PROJECT_ROOT/.git" ] && [ -d "$PROJECT_ROOT/../BearApplicationDepartment/.git" ]; then
         PROJECT_ROOT="$PROJECT_ROOT/../BearApplicationDepartment"
    fi

    cd "$PROJECT_ROOT" || { echo "❌ Failed to navigate to project root"; exit 1; }
fi

echo "📍 Working in: $(pwd)"

# 2. Clean State Check
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ CRITICAL: Uncommitted changes detected."
    echo "   You must start a session from a CLEAN state."
    echo "   Please commit or stash changes before starting."
    git status --short
    exit 1
fi

echo "✅ Git State: Clean"

# 3. Environment Synchronization
echo "🔄 Syncing with origin..."
git fetch origin
git pull origin

# 4. Playbook Sync
if [ -f "BAD/scripts/sync_playbook.sh" ]; then
    echo "📚 Syncing Playbook..."
    chmod +x BAD/scripts/sync_playbook.sh
    ./BAD/scripts/sync_playbook.sh
fi

# 5. Context Rehydration
echo ""
echo "============== HANDOVER =============="
if [ -f "README_HANDOVER.md" ]; then
    cat README_HANDOVER.md
else
    echo "(No handover file found)"
fi
echo "======================================"

echo ""
echo "============== ACTIVE TASKS =============="
if [ -f "task.md" ]; then
    # Show first 10 lines or relevant parts? Just catting for now.
    cat task.md
    # Verify task.md exists in the brain folder? Use the repo root task.md if exists.
    # The artifact system uses a specific path, but on the VM it might be simpler.
    # checking if task.md exists in root.
else
    echo "(No task.md found in root)"
fi
echo "=========================================="

echo ""
echo "✅ SESSION READY."
