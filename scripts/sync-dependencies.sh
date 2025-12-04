#!/bin/bash
# Script to ensure all dependencies are properly synced

set -e

echo "🔧 Syncing project dependencies..."

# Frontend dependencies
echo "📦 Updating frontend dependencies..."
cd frontend
npm ci --include=dev
npm audit fix --audit-level=moderate || true
cd ..

# Backend dependencies  
echo "Updating backend dependencies..."
if command -v uv &> /dev/null; then
    uv sync
else
    pip install -e .
fi

echo "✅ Dependencies synced successfully!"
echo ""
echo "💡 Tips to prevent dependency issues:"
echo "   - Always run 'npm install' after modifying frontend/package.json"
echo "   - Commit package-lock.json changes when you modify dependencies"
echo "   - Use 'npm ci' in Docker/production environments"
echo "   - Run this script before deployment: ./scripts/sync-dependencies.sh"
