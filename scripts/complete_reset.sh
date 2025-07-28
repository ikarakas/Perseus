#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Complete system reset - removes all data including Docker volumes

set -e

echo "🚨 COMPLETE SYSTEM RESET"
echo "========================"
echo ""
echo "This will:"
echo "  1. Stop all containers"
echo "  2. Remove all Docker volumes (postgres_data, telemetry_data, logs)"
echo "  3. Restart containers with fresh databases"
echo ""
echo "⚠️  ALL DATA WILL BE PERMANENTLY LOST!"
echo ""

# Prompt for confirmation
read -p "Are you sure you want to proceed? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operation cancelled"
    exit 1
fi

echo ""
echo "🔄 Stopping containers and removing volumes..."
docker compose down -v

echo ""
echo "🚀 Starting fresh containers..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if services are healthy
echo "🔍 Checking service health..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Services are healthy!"
    echo ""
    echo "🎉 COMPLETE RESET SUCCESSFUL"
    echo ""
    echo "   🌐 Dashboard: http://localhost:8000/dashboard/enhanced"
    echo "   📊 API Docs:  http://localhost:8000/docs"
    echo ""
else
    echo "⚠️  Services may still be starting. Check with:"
    echo "   docker compose ps"
    echo "   docker compose logs"
fi