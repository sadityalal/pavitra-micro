from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from typing import Dict, Any
from shared.auth_middleware import get_current_user
from shared.session_middleware import get_session_id
from .message_consumer import business_alerts
from shared.session_service import session_service, SessionType

router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)):
    user_roles = current_user.get('roles', [])
    if 'admin' not in user_roles and 'super_admin' not in user_roles:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


@router.post("/business/low-stock")
async def send_low_stock_alert(
        product_data: Dict[str, Any],
        background_tasks: BackgroundTasks,
        request: Request,
        current_user: dict = Depends(require_admin)
):
    """Manually trigger low stock alert"""
    try:
        # Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        background_tasks.add_task(
            business_alerts.send_low_stock_alert,
            product_data
        )
        return {"success": True, "message": "Low stock alert queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/test-alert")
async def test_business_alert(
        request: Request,
        current_user: dict = Depends(require_admin)
):
    """Test business alert system"""
    try:
        # Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        test_order = {
            'order_number': 'TEST-123',
            'customer_name': 'Test Customer',
            'customer_email': 'test@example.com',
            'total_amount': 2499.00,
            'item_count': 2,
            'created_at': '2024-01-15 12:00:00',
            'id': 999
        }

        business_alerts.send_new_order_alert(test_order)
        return {"success": True, "message": "Test business alert sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/test-payment")
async def test_payment_alert(
        request: Request,
        current_user: dict = Depends(require_admin)
):
    """Test payment alert system"""
    try:
        # Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        test_payment = {
            'order_number': 'TEST-123',
            'amount': 2499.00,
            'payment_method': 'UPI',
            'status': 'completed',
            'created_at': '2024-01-15 12:00:00'
        }

        business_alerts.send_payment_alert(test_payment)
        return {"success": True, "message": "Test payment alert sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business/test-refund")
async def test_refund_alert(
        request: Request,
        current_user: dict = Depends(require_admin)
):
    """Test refund alert system"""
    try:
        # Update session activity
        session_id = get_session_id(request)
        if session_id:
            session_service.update_session_activity(session_id)

        test_refund = {
            'order_number': 'TEST-123',
            'amount': 2499.00,
            'customer_name': 'Test Customer',
            'reason': 'Test refund',
            'processed_at': '2024-01-15 12:00:00'
        }

        business_alerts.send_refund_alert(test_refund)
        return {"success": True, "message": "Test refund alert sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))