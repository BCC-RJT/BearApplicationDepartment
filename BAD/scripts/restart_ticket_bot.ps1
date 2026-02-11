
$procName = "python"
$scriptName = "src/bridge/tickets_assistant.py"

# Find process running the bot
$processes = Get-WmiObject Win32_Process | Where-Object { $_.Name -eq "$procName.exe" -and $_.CommandLine -like "*$scriptName*" }

if ($processes) {
    Write-Host "Found running bot process(es). Stopping..."
    foreach ($p in $processes) {
        Stop-Process -Id $p.ProcessId -Force
        Write-Host "Stopped process ID $($p.ProcessId)"
    }
}
else {
    Write-Host "No running bot process found."
}

# Start new instance
Write-Host "Starting Ticket Bot..."
$job = Start-Process -FilePath "python" -ArgumentList "$scriptName" -PassThru -NoNewWindow
Write-Host "Bot started with PID $($job.Id)"
