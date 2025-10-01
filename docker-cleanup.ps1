# Clintra Docker Cleanup Script (PowerShell)
# This script removes existing Clintra containers and volumes to prevent conflicts

Write-Host "🧹 Clintra Docker Cleanup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Stop all running Clintra containers
Write-Host "⏹️  Stopping Clintra containers..." -ForegroundColor Yellow
docker compose down 2>$null
if ($LASTEXITCODE -ne 0) {
    docker-compose down 2>$null
}

# Remove all Clintra containers (even if stopped)
Write-Host "🗑️  Removing Clintra containers..." -ForegroundColor Yellow
$containers = @(
    "clintra-backend-1",
    "clintra-frontend-1",
    "clintra-db-1",
    "clintra-pubmed-connector-1",
    "clintra-pubchem-connector-1",
    "clintra-pdb-connector-1",
    "clintra-trials-connector-1"
)

foreach ($container in $containers) {
    docker rm -f $container 2>$null
}

# Remove old images (optional - uncomment if needed)
# Write-Host "🖼️  Removing Clintra images..." -ForegroundColor Yellow
# docker rmi clintra-backend clintra-frontend 2>$null

# Remove volumes (optional - WARNING: This will delete database data)
# Write-Host "💾  Removing Clintra volumes..." -ForegroundColor Yellow
# docker volume rm clintra_postgres_data 2>$null

# Remove network
Write-Host "🌐 Removing Clintra network..." -ForegroundColor Yellow
docker network rm clintra_default 2>$null

# Clean up dangling images and containers
Write-Host "🧼 Cleaning up Docker system..." -ForegroundColor Yellow
docker system prune -f

Write-Host ""
Write-Host "✅ Cleanup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To rebuild and start Clintra:" -ForegroundColor Cyan
Write-Host "  docker compose up --build" -ForegroundColor White
Write-Host ""

