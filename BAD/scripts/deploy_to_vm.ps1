
# Deploy BAD codebase to Antigravity VM
# Usage: .\deploy_to_vm.ps1

$VM_USER = "Headsprung"
$VM_IP = "100.75.180.10"
$LOCAL_ROOT = "c:\Users\Headsprung\Documents\projects\BearApplicationDepartment"
$KEY_PATH = "c:\Users\Headsprung\.ssh\google_compute_engine"
$TarFile = "bad_deploy.tar"

if (-not (Test-Path $TarFile)) {
    Write-Error "File $TarFile not found. Please run 'tar -cf bad_deploy.tar BAD' first."
    exit 1
}

Write-Host "Deploying to $VM_IP..."

# 1. Upload
Write-Host "Uploading payload..."
scp -i $KEY_PATH -o StrictHostKeyChecking=no $TarFile "${VM_USER}@${VM_IP}:/home/${VM_USER}/${TarFile}"

# 2. Unpack
Write-Host "Unpacking on remote..."
ssh -i $KEY_PATH -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" "tar -xf $TarFile && rm $TarFile"

# 3. Sync .env
Write-Host "Syncing .env..."
scp -i $KEY_PATH -o StrictHostKeyChecking=no "$LOCAL_ROOT\.env" "${VM_USER}@${VM_IP}:/home/${VM_USER}/.env"

Write-Host "Deployment Complete."
Write-Host "Installing dependencies..."
ssh -i $KEY_PATH -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" "pip3 install discord.py PyGithub python-dotenv"
