#!/bin/bash
# Deploy BAD codebase to Antigravity VM
# Usage: ./deploy_to_vm.sh

VM_USER="Headsprung"
VM_IP="100.75.180.10"
LOCAL_ROOT="c:/Users/Headsprung/Documents/projects/BearApplicationDepartment"
REMOTE_ROOT="/home/Headsprung/BAD"
SSH_KEY="c:/Users/Headsprung/.ssh/google_compute_engine"

echo "🚀 Deploying to $vm_ip..."

# 1. Sync Files (using scp because rsync might not be on Windows natively in all environments, 
# but if git bash is used, rsync or tar pipe is better. Let's use tar pipe for speed and safety over ssh)

# We will tar the BAD directory and pipe it to untar on remote
echo "📦 Packing and shipping 'BAD' directory..."
tar -cf - -C "$LOCAL_ROOT" BAD | ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" "tar -xf - -C /home/$VM_USER"

# 2. Sync .env (Be careful with secrets!)
echo "🔑 Syncing .env..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$LOCAL_ROOT/.env" "$VM_USER@$VM_IP:$REMOTE_ROOT/../.env"

echo "✅ Code deployed."

# 3. Optional: Restart Service if we had one (We will adding this later)
# ssh ... "sudo systemctl restart bad-bot"

echo "👋 Done."
