#!/bin/bash
set -e

# ==============================================================================
# B.A.D. PROVISIONING SCRIPT - FOUNDATION VM
# ==============================================================================
# MISSION: Provision a production-grade "Worker Node" for the Bear Application Department.
# SPECS: Ubuntu 22.04 LTS | XFCE4 | Chrome | NoMachine | Tailscale | Docker | Python 3.11
# AUTHOR: B.A.D. Lead SRE
# ==============================================================================

# --- CONFIGURATION ---
LOG_FILE="/var/log/bad_provision.log"
NOMACHINE_VERSION="8.11.3_4"
NOMACHINE_DEB="nomachine_${NOMACHINE_VERSION}_amd64.deb"
NOMACHINE_URL="https://download.nomachine.com/download/8.11/Linux/${NOMACHINE_DEB}"
PYTHON_VERSION="3.11"

# --- 1. SETUP & LOGGING ---
# CORE VALUE #2: Observability Is Non-Negotiable
touch "$LOG_FILE"
chmod 600 "$LOG_FILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" | tee -a "$LOG_FILE" >&2
    exit 1
}

# CORE VALUE #1: Reproducibility (Run as Root)
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root. Use sudo."
fi

# Determine the actual user (for directory ownership)
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER="$SUDO_USER"
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
else
    error "Cannot determine actual user. Please run with sudo."
fi

log "Starting provisioning for user: $ACTUAL_USER on $(hostname)"

# --- SYSTEM PREP ---
log "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get upgrade -y
apt-get install -y curl wget gnupg software-properties-common build-essential git ufw

# --- 2. THE VISUAL STACK (The "Eyes") ---
log "Installing XFCE4 and Goodies..."
apt-get install -y xfce4 xfce4-goodies

log "Installing Google Chrome..."
wget -q -O google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb || apt-get install -f -y
rm google-chrome-stable_current_amd64.deb

# Optimization: Disable XFCE Power Management to prevent sleep
log "Disabling Power Management..."
# This is tricky as root regarding user config, but we can set system defaults or hooks.
# For now, we ensure the service doesn't kill the VM connectivity.
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

# --- 3. THE REMOTE BRIDGE (NoMachine) ---
log "Installing NoMachine (${NOMACHINE_VERSION})..."
wget -q "$NOMACHINE_URL" -O "$NOMACHINE_DEB"
if dpkg -i "$NOMACHINE_DEB"; then
    log "NoMachine installed successfully."
else
    log "Fixing NoMachine dependencies..."
    apt-get install -f -y
fi
rm "$NOMACHINE_DEB"

# Configure Firewall
log "Configuring UFW for NoMachine (Port 4000)..."
ufw allow 4000/tcp
ufw allow 22/tcp # Always safe
ufw --force enable

# --- 4. THE NETWORK (Tailscale) ---
log "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh
# Note: User must run `sudo tailscale up` manually to authenticate.

# --- 5. THE RUNTIME (Docker & Python) ---
log "Installing Docker..."
# CORE VALUE #5: Automation Before Headcount (Use official scripts)
curl -fsSL https://get.docker.com | sh
usermod -aG docker "$ACTUAL_USER"

log "Ensuring Python $PYTHON_VERSION..."
# Ubuntu 22.04 ships with 3.10. We need 3.11.
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-venv" "python${PYTHON_VERSION}-dev"
# Make 3.11 available as `python3.11` explicitly.

# --- 6. BAD DIRECTORY SCAFFOLDING ---
log "Scaffolding B.A.D. Directory Structure..."
BAD_ROOT="$USER_HOME/BAD"
mkdir -p "$BAD_ROOT/src"
mkdir -p "$BAD_ROOT/logs"
mkdir -p "$BAD_ROOT/config"
mkdir -p "$BAD_ROOT/playbooks"

# Set permissions
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$BAD_ROOT"

# --- CLEANUP ---
# CORE VALUE #6: Cost Discipline
log "Cleaning up..."
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -f google-chrome-stable_current_amd64.deb

log "Provisioning Complete. Reboot recommended."
log "Next steps for $ACTUAL_USER:"
log "  1. Run 'sudo tailscale up' to connect to the mesh."
log "  2. Reboot to start XFCE/NoMachine services cleanly."
log "  3. Log in via NoMachine."

exit 0
