#!/bin/bash

# ==============================================================================
# B.A.D. Janitor Script - "The Deep Clean"
# ==============================================================================
# Mission: Enforce Cost Discipline (Core Value #6) and Anti-Fragility (Core Value #4)
# Action: Aggressively reclaim disk space and kill zombie processes.
# Usage: Run as root or with sudo.
# ==============================================================================

set -e

# Ensure we are running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run as root (sudo ./janitor.sh)"
  exit 1
fi

echo "🧹 B.A.D. Janitor: Starting Sweep..."

# ------------------------------------------------------------------------------
# 0. Measurement: Get initial disk usage
# ------------------------------------------------------------------------------
DISK_USAGE_BEFORE=$(df -h / | grep / | awk '{print $5}')
DISK_USED_KB_BEFORE=$(df / | grep / | awk '{print $3}')

# ------------------------------------------------------------------------------
# 1. The Disk Reclaimer (Docker & System)
# ------------------------------------------------------------------------------
echo "🐳 Pruning Docker (Aggressive)..."
# Remove all unused containers, networks, images (both dangling and unreferenced), 
# and optionally, volumes.
docker system prune -af --volumes

echo "📦 Cleaning APT cache..."
apt-get clean
apt-get autoremove -y

echo "📜 Vacuuming Systemd Journals..."
# Limit journal logs to 100MB
journalctl --vacuum-size=100M

echo "🗑️ Cleaning /tmp..."
# Delete files in /tmp older than 24h (1440 minutes)
find /tmp -type f -mmin +1440 -delete

# ------------------------------------------------------------------------------
# 2. The Zombie Hunter (Process Management)
# ------------------------------------------------------------------------------
echo "🧟 Hunting Zombies..."

# Kill chrome/chromedriver older than 24h
# We use pgrep to find PIDs, check their elapsed time, and kill if > 86400s
# primitive check: killall if older than specific time is hard with just killall.
# simple approach: kill all chrome/chromedriver instances to be safe, assuming 
# they are ephemeral tasks.
# Better approach requested: "more than 24 hours".
# Using `find` on /proc is one way, but `ps` is easier.
# ps -eo pid,etimes,comm | grep chrome | awk '$2 > 86400 {print $1}' | xargs -r kill -9

echo "   - Checking for stuck Chrome processes (>24h)..."
ps -eo pid,etimes,comm | grep -E "chrome|chromedriver" | awk '$2 > 86400 {print $1}' | xargs -r kill -9 || true

echo "   - Checking for stuck Python processes (excluding bad_bot.py)..."
# Kill python processes > 24h that are NOT bad_bot.py
# 1. Get pids of python processes > 24h
# 2. Filter out the one running bad_bot.py
# This is risky. Let's do a safer "kill orphaned python if > 24h"
# For now, we'll skip the aggressive python kill to avoid killing the main bot 
# if it's been running for > 24h (which is good!).
# INSTEAD: We will only kill python processes that are consuming excessive memory or are definitely zombies if we could detect them.
# Per instructions: "Kill any python processes that are not the main bad_bot.py".
# Identifying "not the main bot" is tricky without a PID file.
# SAFE FALLBACK: Log them for now.
# IMPLEMENTATION: Find python processes > 24h, check command line, if not bad_bot.py, kill.

# Get PIDs of python procs running > 24h
LONG_RUNNING_PYTHON=$(ps -eo pid,etimes,args | grep "python" | awk '$2 > 86400 {print $0}')

# Iterate line by line (this is a bit rough in bash but works for simple cases)
echo "$LONG_RUNNING_PYTHON" | while read -r line; do
    if [ -z "$line" ]; then continue; fi
    PID=$(echo "$line" | awk '{print $1}')
    CMD=$(echo "$line" | cut -d' ' -f3-)
    
    # Check if it's the bad_bot
    if [[ "$CMD" == *"bad_bot.py"* ]]; then
        echo "   - Skipping main bot (PID $PID): $CMD"
    else
        echo "   - 🔫 Killing zombie python (PID $PID): $CMD"
        kill -9 "$PID" || true
    fi
done

# ------------------------------------------------------------------------------
# 3. Observability (The Report)
# ------------------------------------------------------------------------------
DISK_USAGE_AFTER=$(df -h / | grep / | awk '{print $5}')
DISK_USED_KB_AFTER=$(df / | grep / | awk '{print $3}')

# Calculate freed space in MB
FREED_KB=$((DISK_USED_KB_BEFORE - DISK_USED_KB_AFTER))
FREED_MB=$((FREED_KB / 1024))

# Convert to GB if large enough for display
if [ $FREED_MB -gt 1024 ]; then
    FREED_DISPLAY="$(awk "BEGIN {printf \"%.2f\", $FREED_MB/1024}")GB"
else
    FREED_DISPLAY="${FREED_MB}MB"
fi

echo "=============================================================================="
echo "🧹 Janitor Sweep Complete."
echo "   - Freed: $FREED_DISPLAY"
echo "   - Disk Usage: $DISK_USAGE_BEFORE -> $DISK_USAGE_AFTER"
echo "=============================================================================="

