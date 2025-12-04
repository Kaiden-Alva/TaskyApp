#!/bin/bash
set -e

echo "🐘 Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be available with timeout
MAX_TRIES=30
COUNT=0

until pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" > /dev/null 2>&1; do
  COUNT=$((COUNT + 1))
  if [ $COUNT -ge $MAX_TRIES ]; then
    echo "❌ PostgreSQL did not become ready in time"
    exit 1
  fi
  echo "   PostgreSQL is unavailable - waiting (attempt $COUNT/$MAX_TRIES)"
  sleep 2
done

echo "✅ PostgreSQL is ready!"
echo ""
echo "📋 Initializing database..."

# Run database initialization (only seeds if empty)
python init_db.py

echo ""
echo "🚀 Starting Smart Task Manager API..."
echo "   Host: 0.0.0.0"
echo "   Port: 5000"
echo ""

# Start the application
exec uvicorn backend.main:app --host 0.0.0.0 --port 5000

