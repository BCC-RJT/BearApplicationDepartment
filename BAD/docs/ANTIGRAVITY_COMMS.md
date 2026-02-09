# Antigravity Network Communication

This document outlines how to communicate across different "Antigravity Environments" (e.g., Local Dev, Cloud VM, Production) using the dedicated `#antigravity-net` Discord channel.

## Overview

The `#antigravity-net` channel serves as a central bus for:
- Status updates from different environments
- Deployment notifications
- Error alerts
- Cross-agent coordination

## Channel Information

- **Category**: `B.A.D. OPERATIONS`
- **Channel**: `#antigravity-net`
- **Webhook Name**: `Antigravity Uplink`

## Sending Messages via Webhook

You can send messages to this channel from *any* environment without needing a full bot instance, using the Webhook URL.

### Prerequisite

Ensure the `ANTIGRAVITY_WEBHOOK_URL` is set in your `.env` file in the environment you wish to broadcast *from*.

```bash
# .env
ANTIGRAVITY_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Python Example

```python
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv('ANTIGRAVITY_WEBHOOK_URL')

def broadcast_status(environment, status, message):
    if not WEBHOOK_URL:
        print("Webhook URL not configured.")
        return

    payload = {
        "username": f"Antigravity Node ({environment})",
        "embeds": [{
            "title": f"Status Update: {status}",
            "description": message,
            "color": 5814783 if status == "OK" else 15158332 # Green or Red
        }]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Broadcast sent successfully.")
    except Exception as e:
        print(f"Failed to broadcast: {e}")

# Usage
broadcast_status("Local-Dev", "OK", "Boot sequence initiated.")
```

### Curl Example


# Session Start Protocol

When initializing a new environment (e.g., launching a VM, container, or new dev setup), you **MUST** announce your presence to the network.

## Automatic Announcement

We have provided a script `src/bridge/announce_presence.py` that handles this automatically.

### Usage
1. Ensure your `.env` contains `ANTIGRAVITY_WEBHOOK_URL`.
2. run:
   ```bash
   python src/bridge/announce_presence.py
   ```
   
This will post a "New Session Connected" embed to `#antigravity-net` with your hostname and OS details, letting the Controller and other agents know you are online.

## Manual Integration

If you cannot run the python script, you can simply curl the webhook on startup:

```bash
curl -H "Content-Type: application/json" \
     -d '{"username": "Antigravity Node", "content": "🔌 Environment Online: "}' \
     $ANTIGRAVITY_WEBHOOK_URL
```
