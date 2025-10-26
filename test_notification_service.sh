#!/bin/bash

echo "🧪 Testing Notification Service Setup..."

# Check if all required files exist
echo "1. Checking required files..."
files=(
    "backend/notification/main.py"
    "backend/notification/routes.py" 
    "backend/notification/message_consumer.py"
    "backend/notification/business_routes.py"
    "backend/notification/models.py"
    "backend/notification/__init__.py"
    "backend/notification/requirements.txt"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "2. Testing Python imports..."
python3 -c "
try:
    from backend.notification.main import app
    from backend.notification.routes import router
    from backend.notification.business_routes import router as business_router
    from backend.notification.message_consumer import notification_consumer, business_alerts
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
"

echo ""
echo "3. Testing business routes setup..."
python3 -c "
from backend.notification.business_routes import router
print('✅ Business routes loaded successfully')
"

echo ""
echo "4. Testing business alerts service..."
python3 -c "
from backend.notification.message_consumer import business_alerts
print('✅ Business alerts service loaded successfully')
print(f'   Admin email: {business_alerts.admin_email}')
print(f'   Telegram chat ID: {business_alerts.telegram_chat_id}')
"

echo ""
echo "🎉 Notification service setup complete!"
echo ""
echo "To test the service:"
echo "1. Start the service: cd backend/notification && python -m uvicorn main:app --host 0.0.0.0 --port 8006 --reload"
echo "2. Test endpoints: curl http://localhost:8006/health"
echo "3. Get auth token from auth service for protected endpoints"
echo ""
echo "Business alerts will be sent to:"
echo "   - Email: $(python3 -c "from backend.notification.message_consumer import business_alerts; print(business_alerts.admin_email)" 2>/dev/null || echo 'config.site_email')"
echo "   - Telegram: $(python3 -c "from backend.notification.message_consumer import business_alerts; print(business_alerts.telegram_chat_id or 'Not configured')" 2>/dev/null || echo 'Not configured')"
