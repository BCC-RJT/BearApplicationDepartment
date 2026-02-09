# Bear Application Department Bridge Manual

## Overview
The **B.A.D. Bridge** connects our communication center (Discord) with our project memory (GitHub). It ensures that no idea is lost and every task is tracked.

## Architecture
- **Interface:** Discord (`BADbot`)
- **Logic:** Python (`bad_bot.py`) using `discord.py` and `PyGithub`.
- **Memory:** GitHub Issues (`BearApplicationDepartment`).
- **Security:** Tokens loaded from `.env`.

## Usage
The bot listens for a specific command in any channel it has access to.

### Command Syntax
```
!idea [Title] | [Description]
```

### Examples
**1. Standard Idea:**
> `!idea Refactor Login Flow | The current login is too slow. We need to implement OAuth2.`
> *Result:* Creates a GitHub Issue titled **"Refactor Login Flow"** with the body **"The current login is too slow. We need to implement OAuth2."** and replies with the link.

**2. Quick Title Only:**
> `!idea Fix Typo in Header`
> *Result:* Creates a GitHub Issue titled **"Fix Typo in Header"** with the body **"No description provided."**

## Troubleshooting
- **Bot not responding?**
    - Check if the python process is running: `ps aux | grep python` (or check your terminal).
    - Ensure `.env` has valid `DISCORD_TOKEN` and `GITHUB_TOKEN`.
    - Verify "Message Content Intent" is enabled in Discord Developer Portal.
- **Error creating issue?**
    - Check the bot's console output for permission errors.
    - Ensure `GITHUB_TOKEN` has `repo` scope.
