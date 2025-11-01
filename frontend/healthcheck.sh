#!/bin/sh
# Health check script for frontend container

# Check if nginx is running and serving the health endpoint
if wget -q --spider http://localhost/health > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi
