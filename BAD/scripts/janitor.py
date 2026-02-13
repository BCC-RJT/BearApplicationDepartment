import os
import sys
import shutil
import time
import subprocess
import platform
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load Environment (for Webhook)
# Try looking in parent dirs
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # ../
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

WEBHOOK_URL = os.getenv('ANTIGRAVITY_WEBHOOK_URL')
HOSTNAME = platform.node()

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def run_command(cmd, ignore_error=True):
    try:
        if isinstance(cmd, list):
            # On Windows, shell=True is often needed for PATH resolution
            use_shell = platform.system() == 'Windows'
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=use_shell)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        if not ignore_error:
             err_msg = e.stderr if hasattr(e, 'stderr') else str(e)
             log(f"❌ Command failed: {cmd}\n{err_msg}")
        return None

def get_free_space_mb(path):
    try:
        total, used, free = shutil.disk_usage(path)
        return free // (1024 * 1024)
    except:
        return 0

def clean_docker():
    log("🐳 Pruning Docker System...")
    # Version check to see if docker is available
    if run_command("docker --version", ignore_error=True):
        output = run_command("docker system prune -a -f --volumes")
        # Parse output for space reclaimed? 
        # "Total reclaimed space: 1.2GB"
        reclaimed = "0B"
        if output:
            for line in output.split('\n'):
                if "Total reclaimed space:" in line:
                    reclaimed = line.split(":", 1)[1].strip()
        log(f"   ✅ Docker Pruned (Reclaimed: {reclaimed})")
        return reclaimed
    else:
        log("   ⚠️ Docker not found or not running.")
        return "N/A"

def clean_temp_files():
    log("🗑️ Cleaning Temp Files...")
    temp_dir = os.environ.get('TEMP') if os.name == 'nt' else '/tmp'
    
    if not temp_dir or not os.path.exists(temp_dir):
        log("   ⚠️ Temp directory not found.")
        return 0
        
    deleted_count = 0
    reclaimed_bytes = 0
    now = time.time()
    cutoff = now - (24 * 3600) # 24 hours
    
    # Walk and delete
    # On Windows %TEMP% has many locked files, so ignore errors
    for root, dirs, files in os.walk(temp_dir):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                # Check age
                mtime = os.path.getmtime(filepath)
                if mtime < cutoff:
                    try:
                        size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_count += 1
                        reclaimed_bytes += size
                    except OSError:
                        pass # Locked file
            except OSError:
                pass
                
    log(f"   ✅ Deleted {deleted_count} stale files ({reclaimed_bytes / 1024 / 1024:.2f} MB).")
    return reclaimed_bytes

def report_to_uplink(lines_of_text, title="🧹 Janitor Cycle Report"):
    if not WEBHOOK_URL:
        log("⚠️ No Webhook URL found. Skipping report.")
        return
        
    description = "\n".join(lines_of_text)
    
    data = {
        "username": "Janitor Bot",
        "avatar_url": "https://i.imgur.com/8pZ8P9g.png", # Generic broom icon
        "embeds": [{
            "title": title,
            "description": description,
            "color": 3066993, # Greenish Blue
            "footer": {"text": f"Node: {HOSTNAME}"},
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    try:
        requests.post(WEBHOOK_URL, json=data)
        log("📡 Report sent to Uplink.")
    except Exception as e:
        log(f"⚠️ Failed to send report: {e}")

def main():
    log(f"🧹 Janitor Starting on {HOSTNAME} ({platform.system()})...")
    
    start_space = get_free_space_mb(".")
    
    # 1. Docker
    docker_reclaimed = clean_docker()
    
    # 2. Temp
    temp_bytes = clean_temp_files()
    temp_mb = temp_bytes / (1024 * 1024)
    
    end_space = get_free_space_mb(".")
    freed_total = end_space - start_space
    
    # Report
    summary = [
        f"**Node**: `{HOSTNAME}`",
        f"**System**: `{platform.system()} {platform.release()}`",
        "",
        "**Actions**:",
        f"🐳 **Docker Prune**: RECLAIMED `{docker_reclaimed}`",
        f"🗑️ **Temp Clean**: FREED `{temp_mb:.2f} MB`",
        "",
        f"**Total Disk Free**: `{end_space} MB` (Change: +{freed_total} MB)"
    ]
    
    report_to_uplink(summary)
    log("✨ Cycle Complete.")

if __name__ == "__main__":
    main()
