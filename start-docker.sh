#!/bin/bash
echo "🚀 Starting Pavitra Trading with Docker..."

# Stop existing containers
docker-compose down

# Build and start
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 15

echo "🔍 Checking services..."
curl -f http://localhost:8001/health && echo "✅ Backend is running!"
curl -f http://localhost:3306 && echo "✅ MySQL is running!" || echo "❌ MySQL not accessible"

echo ""
echo "🌐 Services:"
echo "   Backend API: http://localhost:8001"
echo "   MySQL: localhost:3306"
echo "   Redis: localhost:6379"
echo ""
echo "🛑 Stop with: docker-compose down"
