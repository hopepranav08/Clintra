#!/bin/bash

# Clintra Docker Cleanup Script
# This script removes existing Clintra containers and volumes to prevent conflicts

echo "🧹 Clintra Docker Cleanup Script"
echo "================================"
echo ""

# Stop all running Clintra containers
echo "⏹️  Stopping Clintra containers..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null

# Remove all Clintra containers (even if stopped)
echo "🗑️  Removing Clintra containers..."
docker rm -f clintra-backend-1 clintra-frontend-1 clintra-db-1 \
    clintra-pubmed-connector-1 clintra-pubchem-connector-1 \
    clintra-pdb-connector-1 clintra-trials-connector-1 2>/dev/null

# Remove old images (optional - uncomment if needed)
# echo "🖼️  Removing Clintra images..."
# docker rmi clintra-backend clintra-frontend 2>/dev/null

# Remove volumes (optional - WARNING: This will delete database data)
# echo "💾  Removing Clintra volumes..."
# docker volume rm clintra_postgres_data 2>/dev/null

# Remove network
echo "🌐 Removing Clintra network..."
docker network rm clintra_default 2>/dev/null

# Clean up dangling images and containers
echo "🧼 Cleaning up Docker system..."
docker system prune -f

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To rebuild and start Clintra:"
echo "  docker compose up --build"
echo ""

