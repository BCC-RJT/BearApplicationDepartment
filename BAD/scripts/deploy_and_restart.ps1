# deploy_and_restart.ps1
# Full CD pipeline: Deploys code and restarts services on foundation-vm

Write-Host ">>> Starting Full Deployment Pipeline <<<"

# 1. Deploy code
.\deploy_to_vm.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment failed!"
    exit 1
}

# 2. Restart Services
$VM_NAME = "foundation-vm"
$ZONE = "us-central1-a"

Write-Host "Restarting Services on $VM_NAME..."
# Restart Ticket Assistant and Architect services
# Assuming systemd units are named 'bad-ticket-assistant' and 'bad-architect'
# Or just kill python processes if untracked.
# Since we want to SUSPEND Project Planner, we will force kill it and only restart Ticket Assistant if needed.
# Actually, Ticket Assistant is local-only now.
# So we only need to restart BADbot (Ops) if it's there. Project Planner should stay dead.

# COMMAND: Kill everything to refresh
gcloud compute ssh $VM_NAME --zone=$ZONE --tunnel-through-iap --command="pkill -f python; nohup python3 src/bridge/bad_bot.py > logs/bad_bot.log 2>&1 &"

Write-Host "Deployment & Restart Complete!"
