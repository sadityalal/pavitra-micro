#!/bin/sh
# Health check for frontend
if wget -q --spider http://localhost:80; then
    exit 0
else
    exit 1
fi