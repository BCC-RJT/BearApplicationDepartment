
import psutil
import sys
import subprocess
import time

def kill_process(name_contains):
    killed = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and name_contains in ' '.join(cmdline):
                print(f"Killing process {proc.info['pid']}: {cmdline}")
                proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return killed

if __name__ == "__main__":
    target = "tickets_assistant.py"
    print(f"Searching for {target}...")
    if kill_process(target):
        print("Process killed.")
    else:
        print("Process not found.")
    
    # Restart
    print("Restarting bot...")
    # Using subprocess.Popen to start in background essentially
    # But wait, run_command does that.
    # So I just exit and let run_command handle the restarting if user approves?
    # No, I should restart it via run_command after this script finishes.
