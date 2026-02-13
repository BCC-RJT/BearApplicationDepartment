# deploy_to_vm.ps1 (Refactored for GCloud IAP)
# Deploys code to foundation-vm (takeoff-specialist)

$VM_NAME = "foundation-vm"
$ZONE = "us-central1-a"

Write-Host "Creating deployment tarball..."
# Exclude venv, .git, __pycache__, logs, data to keep it small
tar --exclude='venv' --exclude='.git' --exclude='__pycache__' --exclude='logs' --exclude='data' -cf bad_deploy.tar .

Write-Host "Uploading tarball to $VM_NAME..."
gcloud compute scp bad_deploy.tar ${VM_NAME}:~/bad_deploy.tar --zone=$ZONE --tunnel-through-iap

Write-Host "Extracting and Installing on $VM_NAME..."
gcloud compute ssh $VM_NAME --zone=$ZONE --tunnel-through-iap --command="tar -xf bad_deploy.tar && rm bad_deploy.tar && pip3 install -r requirements.txt"

Write-Host "Deployment Complete!"
# Clean up local tar
Remove-Item bad_deploy.tar
