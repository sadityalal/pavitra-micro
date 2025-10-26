#!/bin/bash
# Simple test runner for Payment Service

echo "🔧 Setting up Python path..."
export PYTHONPATH="$PYTHONPATH:$(pwd)"

echo "🚀 Starting Payment Service Tests..."
python backend/payment/test_secure_payment.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ Tests completed successfully!"
else
    echo "❌ Tests failed!"
    exit 1
fi
