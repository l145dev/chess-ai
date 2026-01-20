# azure/server-to-cloud.ps1
# Note: run from root

# Configuration
$vmIp = "20.199.136.72"
$keyPath = "azure/chessbot-backend_key.pem"
$remoteUser = "azureuser"
$tempDir = "dist_backend_temp"

Write-Host "Starting Deployment to Azure ($vmIp)..." -ForegroundColor Cyan

# 1. Clean up & Create Temp Directory Structure
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
# We need to create the specific subfolders so Copy-Item knows where to put things
New-Item -ItemType Directory -Force -Path "$tempDir/engines/bot/model" | Out-Null
New-Item -ItemType Directory -Force -Path "$tempDir/server" | Out-Null

# 2. Bundle Files (The Surgical Approach)
Write-Host "Bundling ONLY necessary files..." -ForegroundColor Yellow

# Move Dockerfile to root
Copy-Item "azure/Dockerfile" -Destination "$tempDir/Dockerfile"

# Move Caddyfile to root
Copy-Item "azure/Caddyfile" -Destination "$tempDir/Caddyfile"

# Copy specific engine files
Write-Host "   -> Copying Engine Core..." -ForegroundColor Gray
Copy-Item "engines/bot/model/mlp_model.pth" -Destination "$tempDir/engines/bot/model/"
Copy-Item "engines/bot/main.py"             -Destination "$tempDir/engines/bot/"
Copy-Item "engines/bot/search.py"           -Destination "$tempDir/engines/bot/"
Copy-Item "engines/bot/model.py"            -Destination "$tempDir/engines/bot/"
Copy-Item "engines/bot/dataset.py"          -Destination "$tempDir/engines/bot/"

# Copy server files
Write-Host "   -> Copying API Server..." -ForegroundColor Gray
# Exclude tests folder
Copy-Item "server/*" -Destination "$tempDir/server" -Recurse -Exclude "tests"

# Copy root files
Copy-Item ".env" -Destination "$tempDir"
Copy-Item "requirements.txt" -Destination "$tempDir"

# 3. Upload to Azure
Write-Host "☁️ Uploading payload..." -ForegroundColor Yellow
# Remove old build folder on server first
ssh -i $keyPath -o StrictHostKeyChecking=no ${remoteUser}@${vmIp} "rm -rf ~/chessbot_build"
# Upload new clean bundle
scp -i $keyPath -r $tempDir "${remoteUser}@${vmIp}:~/chessbot_build"

# 4. Build & Run
Write-Host "Building and Running on VM..." -ForegroundColor Yellow
$commands = @(
    "cd ~/chessbot_build",
    # Create network
    "sudo docker network create chess-net || true",
    
    # Build Bot
    "sudo docker build -t chess-backend .",
    
    # Stop Old Containers
    "sudo docker rm -f caddy-container chess-backend-container || true",
    
    # Run Bot (Internal Only)
    "sudo docker run -d --net chess-net --name chess-backend-container --restart always chess-backend",
    
    # Run Caddy (Public HTTPS Gateway)
    "sudo docker run -d -p 80:80 -p 443:443 --net chess-net --name caddy-container --restart always -v `$(pwd)/Caddyfile:/etc/caddy/Caddyfile -v caddy_data:/data caddy:alpine"
)

ssh -i $keyPath ${remoteUser}@${vmIp} ($commands -join " && ")

# 5. Cleanup Local Temp
Remove-Item -Recurse -Force $tempDir
Write-Host "✅ Deployment Complete!" -ForegroundColor Green