#!/bin/bash

# Session End Script (VM Side)
# Enforces Protocol: END_OF_SESSION (PHASE-02)

set -e

# 1. Location Check (Reusing robust logic from session_start.sh)
if git rev-parse --show-toplevel > /dev/null 2>&1; then
    PROJECT_ROOT=$(git rev-parse --show-toplevel)
    echo "✅ Using CWD as Root: $PROJECT_ROOT"
else
    # Fallback
    SCRIPT_DIR="$(dirname "$(realpath "$0")")"
    PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
    
    # VM Fix: Check if we are in ~/BAD and repo is ~/BearApplicationDepartment
    if [ ! -d "$PROJECT_ROOT/.git" ] && [ -d "$PROJECT_ROOT/../BearApplicationDepartment/.git" ]; then
         PROJECT_ROOT="$PROJECT_ROOT/../BearApplicationDepartment"
    fi

    cd "$PROJECT_ROOT" || { echo "❌ Failed to navigate to project root"; exit 1; }
fi

echo "📍 Working in: $(pwd)"
COMMIT_MSG="${1:-chore: End of Session Backup $(date +'%Y-%m-%d %H:%M')}"

# 2. Check for Changes
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ Git State: Clean (No changes to commit)"
else
    echo "🔄 Uncommitted changes detected. Committing..."
    git add .
    git commit -m "$COMMIT_MSG"
    echo "✅ Changes committed."
fi

# 3. Configure Auth & Push
if [ -n "$GITHUB_TOKEN" ] && [ -n "$REPO_NAME" ]; then
    echo "🔐 Configuring Remote Auth..."
    git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${REPO_NAME}.git"
else
    echo "⚠️ GITHUB_TOKEN or REPO_NAME missing. Pushing might fail if not authenticated."
fi

echo "🔄 Pushing to origin..."
git push origin || { echo "❌ Push failed. Check your token permissions."; exit 1; }

echo "✅ Session Closed Successfully."
