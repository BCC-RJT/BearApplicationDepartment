# Troubleshooting Discord Navigation Issues

## Problem
A user reports that "Antigravity won't navigate to discord.com due to a system security policy."

## Context
The "System Security Policy" error typically originates from the **Operating System (Windows)** or a **Group Policy** when an application attempts to launch a web browser or navigate to a specific URL.

Since the `BAD` codebase (including `ticket_bot`, `bridge`, and `scripts`) does **not** contain independent browser automation (like Selenium/Playwright) that navigates to Discord, this error most likely occurs when:

1.  **Clicking a Link in Terminal/VS Code:** The user clicks an Invite Link printed by `fix_architect_setup.py` or similar scripts, and the editor/terminal is blocked from opening the default browser.
2.  **Antigravity Agent Browser:** The AI Agent itself tries to open a browser window, and the underlying browser (Chromium/Chrome) is restricted by AppLocker or Firewall rules on the user's machine.

## Solutions

### 1. "This operation has been cancelled due to restrictions in effect on this computer"
**Symptoms:** Clicking a link in VS Code or Terminal (e.g., the Bot Invite link) pops up a Windows alert with this message.

**Fixes:**
*   **Check Default Browser:** Ensure a valid default browser (Chrome/Edge) is set in Windows Settings -> Apps -> Default Apps.
*   **VS Code Trusted Domains:** If using VS Code, ensure `discord.com` is in the trusted domains if prompted (though usually this doesn't trigger a system policy error).
*   **Corporate Policy (IT):** If on a work machine, IT may have blocked the terminal application (e.g., `cmd.exe`, `powershell.exe`, or `Code.exe`) from launching browser processes via AppLocker.
    *   *Workaround:* Copy the link manually and paste it into an open browser window.

### 2. Browser "Blocked" Page
**Symptoms:** The browser opens, but displays a "Blocked" or "Access Denied" page (e.g., from Zscaler, Cisco Umbrella, or generic Firewall).

**Fixes:**
*   **Network Check:** Try accessing `discord.com` from a personal device on the same network (if Wi-Fi) to rule out network-wide blocks.
*   **VPN:** Disconnect from corporate VPNs if allowed.

### 3. Antigravity Agent Troubleshooting
If the "Antigravity" refers to the AI Agent failing to verify a step involving Discord:

*   **Headless Browser Detection:** Some sites (like Discord) block headless browsers (used by some automation tools).
    *   *Check:* Ensure the agent is running in "Headful" mode if possible (though the user cannot typically configure this for the standard agent).
*   **Local Firewall:** Check if `python.exe` or the Agent's process is blocked by Windows Defender Firewall.

## Diagnostic Steps for the User
Ask the user to run the following checks:

1.  **Manual Navigation:** Can you open `https://discord.com` in your regular Chrome/Edge browser?
2.  **Link Copy-Paste:** If you copy the link from the Antigravity output and paste it into the browser, does it work?
    *   *If YES:* The issue is the "Click-to-Open" mechanism in their terminal/IDE, not the network.
    *   *If NO:* The issue is a network/site block.

## Summary
The "System Security Policy" error is almost certainly local to the user's machine configuration (OS restrictions on launching apps) rather than a bug in the `BAD` code.
