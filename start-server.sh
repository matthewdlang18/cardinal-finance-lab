#!/bin/bash

# Cardinal Finance Lab - Server Startup Script
# This script starts the backend server for the Stock Analysis Lab

cd "$(dirname "$0")"

echo "🎓 Starting Cardinal Finance Lab Server..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Kill any existing server on port 3001
if lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null ; then
    echo "🔄 Stopping existing server on port 3001..."
    lsof -ti:3001 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "Please create a .env file with your POLYGON_API_KEY"
    exit 1
fi

# Start the server
echo "🚀 Starting server on http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "📊 Pages available:"
echo "   • Personal Finance: index.html"
echo "   • Stock Analysis: stock-analysis.html"
echo "   • Test API: test-api.html"
echo "   • Start Page: start.html"
echo ""

node server.js
