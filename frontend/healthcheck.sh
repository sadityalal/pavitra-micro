#!/bin/sh

# Health check for the container
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    exit 0
else
    exit 1
fi