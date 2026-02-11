# Deploy and Restart Ticket Assistant on VM
# Usage: .\deploy_and_restart.ps1

$VM_USER = "Headsprung"
$VM_IP = "100.75.180.10"
$KEY_PATH = "c:\Users\Controller\.ssh\google_compute_engine"
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $ScriptDir).Parent.Parent.FullName # BearApplicationDepartment root

Write-Host "🚀 Deploying updates to VM ($VM_IP)..."

# 1. Run standard deployment
# Assuming deploy_to_vm.ps1 is in the same directory
& "$ScriptDir\deploy_to_vm.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed."
    exit 1
}

Write-Host "🔄 Restarting Ticket Assistant Service..."

# 2. Remote Command Execution
# Kill existing python process for tickets_assistant.py
# Start new process in background using nohup
# Note: Using pkill -f might be aggressive, but effective for this setup.

$RemoteCommand = "pkill -f 'tickets_assistant.py'; pkill -f 'bad_bot.py'; nohup python3 BAD/src/bridge/tickets_assistant.py > BAD/logs/tickets_assistant.log 2>&1 & nohup python3 BAD/src/bridge/bad_bot.py > BAD/logs/bad_bot.log 2>&1 &"

ssh -i $KEY_PATH -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" $RemoteCommand

Write-Host "✅ Service Restart Command Sent."
Write-Host "   Check logs on VM: tail -f BAD/logs/tickets_assistant.log"
