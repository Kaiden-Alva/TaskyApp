#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Get the branch name from the first argument (defaults to main if not provided)
BRANCH=${1:-main}

# Navigate to the project directory
cd ./CS2450Project

# Pull the latest changes from the specified branch
echo "Pulling latest changes from $BRANCH branch..."
git checkout "$BRANCH"
git pull origin "$BRANCH"

# Rebuild and restart the docker-compose services
# Use "docker compose" (with a space) for the plugin version
echo "Rebuilding and restarting Docker services..."
# Remove old volumes to ensure clean dependency installation
docker compose down -v
docker compose --profile web up -d --build

echo "Cleaning up unused Docker resources..."
docker image prune -f

echo "Deployment completed successfully."