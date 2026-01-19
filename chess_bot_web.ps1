$ErrorActionPreference = "Stop"

$rootPath = $PSScriptRoot
$chatbotPath = Join-Path $rootPath "chatbot"

# 1. Check/Install node_modules
Write-Host "Checking for node_modules in $chatbotPath..."
if (-not (Test-Path (Join-Path $chatbotPath "node_modules"))) {
    Write-Host "node_modules not found. Installing dependencies..."
    Push-Location $chatbotPath
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "npm install failed!"
        Pop-Location
        exit 1
    }
    Pop-Location
} else {
    Write-Host "node_modules found."
}

# 2. Start Astro Dev Server
Write-Host "Starting Astro Dev Server..."
# Opens in a new window, keeps it open (-NoExit)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$chatbotPath'; npm run dev"

# 3. Start Python Engine
Write-Host "Starting Python Chess Engine..."
# Runs from root, opens in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$rootPath'; python -m server.main"

Write-Host "Servers started in separate windows."
