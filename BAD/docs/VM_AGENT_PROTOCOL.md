# Agent VM Access Protocol

## Overview
This document defines how the AI Agent (`Antigravity`) should "see" and "interact" with the "Antigravity VM" (`foundation-vm` / `bad-node-01`).

## 1. Terminal Interaction (Preferred)
**Method:** SSH
**Reliability:** High
**Use Case:** Running scripts, checking files, installing software, system monitoring.
**Command:**
```bash
ssh -i "c:\Users\Headsprung\.ssh\google_compute_engine" -o StrictHostKeyChecking=no Headsprung@100.75.180.10 "COMMAND"
```

## 2. Web App Interaction (Preferred for Testing)
**Method:** Direct Browser Access
**Reliability:** High
**Use Case:** Testing web applications running on the VM.
**How:**
1.  Target App runs on VM Port (e.g., 3000).
2.  Agent Browser visits `http://100.75.180.10:3000`.
3.  Agent interacts with **Real DOM**.

## 3. Desktop GUI Interaction (Fallback)
**Method:** noVNC via Browser Subagent
**Reliability:** Moderate (Canvas-based)
**Use Case:** Verifying visual states that cannot be captured via terminal or web app (e.g., browser rendering bugs, OS dialogs).

### Critical Protocol for noVNC
When accessing `http://100.75.180.10:6080/vnc.html`:
1.  **Blind Login:** Do NOT wait for a "Logged In" DOM element. The Canvas is opaque.
    *   Click "Connect".
    *   Wait 2s.
    *   Type Password (`bear123`).
    *   Click Submit.
    *   Wait 5s.
2.  **Verification:** Use `capture_browser_screenshot`. **Do not use `browser_get_dom` to verify state.**
3.  **Interaction:** Use `click_browser_pixel` (X,Y coordinates) based on screenshot analysis.

### Coordinates Reference (1280x800)
- **Login Password Field:** Center Screen (~500, ~500)
