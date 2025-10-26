try {
    python lichess-bot.py
} catch {
    Write-Host "python command failed, trying python3..."
    python3 lichess-bot.py
}