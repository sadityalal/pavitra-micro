from fastapi import APIRouter, HTTPException, Depends, Form, Request, status, BackgroundTasks
from typing import Optional
from datetime import datetime, timedelta
from shared import (
    config, db, verify_password, get_password_hash,
    create_access_token, verify_token, validate_email,
    validate_phone, sanitize_input, get_logger, rabbitmq_client
)
from .models import (
    UserCreate, UserLogin, Token, UserResponse,
    RoleResponse, PermissionCheck, HealthResponse
)

router = APIRouter()
logger = get_logger(__name__)

def publish_user_registration_event(user_data: dict):
    """Publish user registration event to RabbitMQ"""
    try:
        message = {
            'event_type': 'user_registered',
            'user_id': user_data['id'],
            'email': user_data.get('email'),
            'first_name': user_data.get('first_name'),
            'timestamp': datetime.utcnow().isoformat(),
            'data': user_data
        }
        
        rabbitmq_client.publish_message(
            exchange='notification_events',
            routing_key='user.registered',
            message=message
        )
        logger.info(f"User registration event published for user {user_data['id']}")
    except Exception as e:
        logger.error(f"Failed to publish user registration event: {e}")

# [Rest of the existing auth routes code remains the same until the register endpoint...]

@router.post("/register", response_model=Token)
async def register_user(
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    country_id: int = Form(1),
    background_tasks: BackgroundTasks = None
):
    first_name = sanitize_input(first_name)
    last_name = sanitize_input(last_name)
    if not email and not phone and not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email, phone, or username is required"
        )
    if email and not validate_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    if phone and not validate_phone(phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone format"
        )
    if username and not validate_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3-30 characters and contain only letters, numbers, and underscores"
        )
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    try:
        with db.get_cursor() as cursor:
            if email:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            if phone:
                cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Phone number already registered"
                    )
            if username:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already taken"
                    )
            password_hash = get_password_hash(password)
            cursor.execute("""
                INSERT INTO users (email, phone, username, password_hash, first_name, last_name, country_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email, phone, username, password_hash, first_name, last_name, country_id))
            user_id = cursor.lastrowid
            cursor.execute("SELECT id FROM user_roles WHERE name = 'customer'")
            role = cursor.fetchone()
            if role:
                cursor.execute("""
                    INSERT INTO user_role_assignments (user_id, role_id, assigned_by)
                    VALUES (%s, %s, %s)
                """, (user_id, role['id'], user_id))
            cursor.execute("""
                SELECT ur.name as role_name, p.name as permission_name
                FROM user_role_assignments ura
                JOIN user_roles ur ON ura.role_id = ur.id
                LEFT JOIN role_permissions rp ON ur.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                WHERE ura.user_id = %s
            """, (user_id,))
            roles = set()
            permissions = set()
            for row in cursor.fetchall():
                if row['role_name']:
                    roles.add(row['role_name'])
                if row['permission_name']:
                    permissions.add(row['permission_name'])
            access_token = create_access_token(
                data={
                    "sub": str(user_id),
                    "email": email,
                    "roles": list(roles),
                    "permissions": list(permissions)
                },
                expires_delta=timedelta(hours=24)
            )
            
            # Get created user
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            # Publish user registration event in background
            if background_tasks:
                background_tasks.add_task(
                    publish_user_registration_event,
                    user
                )
            
            logger.info(f"User registered successfully: {email or phone or username}")
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=86400,
                user_roles=list(roles),
                user_permissions=list(permissions)
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

# [Rest of the existing auth routes remain the same...]
