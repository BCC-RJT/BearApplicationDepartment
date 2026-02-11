import os
import requests
import socket
import platform
from dotenv import load_dotenv

# Setup
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to find the actual repo root
candidate_root = os.path.dirname(PROJECT_ROOT) # Default parent
if os.path.isdir(os.path.join(candidate_root, ".git")):
    REPO_ROOT = candidate_root
elif os.path.isdir(os.path.join(candidate_root, "BearApplicationDepartment")):
    REPO_ROOT = os.path.join(candidate_root, "BearApplicationDepartment")
else:
    REPO_ROOT = PROJECT_ROOT

ENV_PATH = os.path.join(REPO_ROOT, '.env')
if not os.path.exists(ENV_PATH):
     ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

load_dotenv(ENV_PATH)

WEBHOOK_URL = os.getenv('ANTIGRAVITY_WEBHOOK_URL')

def announce_presence():
    if not WEBHOOK_URL:
        print("❌ ANTIGRAVITY_WEBHOOK_URL not configured. Cannot announce presence.")
        return

    hostname = socket.gethostname()
    os_name = platform.system()
    release = platform.release()

    goal_status = "⚠️ BLOCKED: Connection Timeout to 100.75.180.10. Seeking info from successful teams."
    
    payload = {
        "username": "Antigravity Node",
        "embeds": [{
            "title": "🔌 New Session Connected",
            "description": f"An environment has come online and is ready for instructions.",
            "color": 3447003, # Blue
            "fields": [
                {"name": "Hostname", "value": hostname, "inline": True},
                {"name": "OS", "value": f"{os_name} {release}", "inline": True},
                {"name": "Root Path", "value": REPO_ROOT, "inline": False},
                {"name": "🏔️ Global Session Goal", "value": goal_status, "inline": False}
            ],
            "footer": {"text": "Antigravity Network Coordination Protocol v1.1"}
        }]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"✅ Presence announced from {hostname}")
        
        # Also post a specific inquiry as a regular message to ping the team
        inquiry = {
            "content": "🚨 **CROSS-TEAM INQUIRY**: One of our teams is reporting a timeout to the VM at `100.75.180.10`. If your team has successfully restarted the server in a previous session, please reply with your connection method (Tailscale status, SSH config, or Tunnel info)."
        }
        requests.post(WEBHOOK_URL, json=inquiry)
    except Exception as e:
        print(f"⚠️ Failed to announce presence: {e}")

if __name__ == "__main__":
    announce_presence()
