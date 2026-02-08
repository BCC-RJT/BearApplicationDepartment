
# Connect to Antigravity VM (bad-node-01)
$User = "Headsprung"
$IP = "100.75.180.10"
$Key = "c:\Users\Headsprung\.ssh\google_compute_engine"

Write-Host "Connecting to Antigravity VM ($IP)..."
ssh -i $Key -o StrictHostKeyChecking=no $User@$IP
