#!/bin/bash

# kill_switch.sh
# Terminates non-essential processes (Chrome, unknown Python)
# Preserves bad_bot.py and the current shell

LOG_FILE="kill_switch.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

echo "[$TIMESTAMP] 🚨 KILL SWITCH ACTIVATED" | tee -a "$LOG_FILE"

# 1. Kill Chrome Processes
echo "[$TIMESTAMP] Searching for Chrome processes..." | tee -a "$LOG_FILE"
# Check if pkill is available (it should be in most bash envs)
if command -v pkill &> /dev/null; then
    pkill -9 -f "chrome"
    if [ $? -eq 0 ]; then
        echo "[$TIMESTAMP] ✅ Killed Chrome processes." | tee -a "$LOG_FILE"
    else
        echo "[$TIMESTAMP] ℹ️ No Chrome processes found or failed to kill." | tee -a "$LOG_FILE"
    fi
else
    # Fallback to visual basic or windows specific if needed, but assuming bash environment
    # Using taskkill for Windows compatibility if running in Git Bash/WSL pointing to Windows processes?
    # The prompt requested a .sh file, implying bash. I'll stick to standard bash tools.
    # But if it's Windows Git Bash, pkill might not catch Windows processes perfectly without .exe extension.
    # Let's try both 'chrome' and 'chrome.exe' just in case if using pkill
    pkill -9 -f "chrome.exe"
fi


# 2. Kill Python Processes (Except bad_bot.py)
echo "[$TIMESTAMP] Searching for rogue Python processes..." | tee -a "$LOG_FILE"

# Get own PID and bad_bot.py PID to exclude
# We find pids matching python
# We iterate and check command line
# This implementation uses pgrep -a to list full command line

# Process listing might vary by OS. 
# Using a loop over pids.

# Note: In Windows Git Bash, ps -W might be needed to see windows processes.
# But sticking to standard linux-like syntax for the requested .sh
# logic: list all python processes, filter out bad_bot.py, kill remainder.

pids=$(pgrep -f "python")

for pid in $pids; do
    # Get command line for this pid
    cmdline=$(ps -p "$pid" -o args= 2>/dev/null || cat /proc/$pid/cmdline 2>/dev/null)
    
    if [[ "$cmdline" == *bad_bot.py* ]]; then
        echo "[$TIMESTAMP] 🛡️ Shielding bad_bot.py (PID: $pid)" | tee -a "$LOG_FILE"
    else
        echo "[$TIMESTAMP] 🔫 Terminating PID $pid: $cmdline" | tee -a "$LOG_FILE"
        kill -9 "$pid"
    fi
done

echo "[$TIMESTAMP] 🏁 Kill switch sequence complete." | tee -a "$LOG_FILE"
