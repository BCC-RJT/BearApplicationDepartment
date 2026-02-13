# Connect to Foundation VM via IAP Tunnel
Write-Host "Connecting to foundation-vm (takeoff-specialist) via gcloud IAP..."
gcloud compute ssh foundation-vm --tunnel-through-iap
