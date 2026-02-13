# start_ticket_bot.ps1

param (
    [string]$Environment = "dev",
    [switch]$Local = $false
)

# Set location to script directory
Set-Location $PSScriptRoot

# --- Configuration ---
if ($Environment -eq "main") {
    $EnvFile = ".env.main"
    $ContainerName = "ticket-assistant-main"
    $EnvTokenName = "TICKET_ASSISTANT_TOKEN" # Though Prod usually uses Docker env passing
    Write-Host "Target Environment: MAIN"
}
elseif ($Environment -eq "dev") {
    $EnvFile = ".env.dev" # Or just .env for local
    $ContainerName = "ticket-assistant-dev"
    $EnvTokenName = "TICKET_ASSISTANT_TOKEN"
    Write-Host "Target Environment: DEV"
}
else {
    Write-Error "Error: Unknown environment '$Environment'. Use 'dev' or 'main'."
    exit 1
}

# --- Local Execution Mode ---
if ($Local) {
    Write-Host "--- STARTING LOCALLY (Python Direct) ---"
    
    # Check for Python
    if (-not (Get-Command "py" -ErrorAction SilentlyContinue) -and -not (Get-Command "python" -ErrorAction SilentlyContinue)) {
        Write-Error "Python not found! Please install Python."
        exit 1
    }

    # Load .env variables manually for PowerShell session if needed
    # Better: Use the --dev flag which tickets_assistant.py uses to load .env, 
    # BUT we need to inject the specific TOKEN into the process environment if it's not in .env correctly.
    # We standardized .env to have TICKET_ASSISTANT_TOKEN, so the python script should pick it up via os.getenv.
    
    # We just run the script. The script's 'if --dev' block handles the rest.
    # However, to be safe and match run_dev.ps1's behavior, we explicitly set the token env var if available in current shell,
    # but since we moved to a robust .env, we can just trust the python script to load .env.
    
    Write-Host "Launching src/bridge/tickets_assistant.py --dev..."
    
    # Use 'py' if available, else 'python'
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        py src/bridge/tickets_assistant.py --dev
    }
    else {
        python src/bridge/tickets_assistant.py --dev
    }
    
    exit 0
}

# --- Docker Execution Mode ---
if (-not (Test-Path $EnvFile)) {
    # If .env.dev doesn't exist, try .env
    if (Test-Path ".env") {
        $EnvFile = ".env"
        Write-Host "Config file '$Environment' not found, falling back to '.env'."
    }
    else {
        Write-Error "Error: Configuration file '$EnvFile' not found!"
        exit 1
    }
}

Write-Host "Building Ticket Assistant (Docker)..."
docker build -t ticket-assistant .

Write-Host "Starting Ticket Assistant ($ContainerName)..."

# Stop/Remove existing container
$existing = docker ps -aq -f "name=^/${ContainerName}$"
if ($existing) {
    Write-Host "Stopping existing container..."
    docker rm -f $ContainerName
}

# Run Container
$CurrentDir = Get-Location
docker run -d `
    --name $ContainerName `
    --restart unless-stopped `
    -v "$CurrentDir/data:/app/data" `
    --env-file "$EnvFile" `
    ticket-assistant

Write-Host "Bot started in Docker! Logs:"
docker logs -f $ContainerName
