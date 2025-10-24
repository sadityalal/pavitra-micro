import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Form, UploadFile, File, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging
import mysql.connector
from mysql.connector import Error
import shutil
import uuid

sys.path.append('/app')
from shared.utils.config import config
from shared.database.database import db
from shared.utils.logger import get_user_logger
from shared.security.password_utils import PasswordSecurity
from shared.security.role_checker import allow_authenticated, RoleChecker
from shared.models.user_models import UserResponse

logger = get_user_logger()

app = FastAPI(
    title="User Service - Pavitra Trading",
    description="User Profile Management Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    country_id: Optional[int] = None
    preferred_currency: Optional[str] = None
    preferred_language: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class AddressCreate(BaseModel):
    address_type: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    country: str = "India"
    postal_code: str
    is_default: bool = False

@app.get("/")
async def root():
    return {"message": "User Service - Pavitra Trading", "environment": config.app_env}

@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return {
            "status": "healthy",
            "service": "user",
            "environment": config.app_env,
            "users_count": user_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "user",
            "environment": config.app_env
        }

@app.get("/profile", response_model=UserResponse)
async def get_user_profile(payload: dict = Depends(allow_authenticated)):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.id, u.uuid, u.email, u.first_name, u.last_name, u.phone, u.username,
                   u.country_id, u.is_active, u.email_verified, u.phone_verified,
                   u.preferred_currency, u.preferred_language, u.avatar_url,
                   u.created_at, u.updated_at
            FROM users u
            WHERE u.id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user roles
        cursor.execute("""
            SELECT ur.name 
            FROM user_roles ur
            JOIN user_role_assignments ura ON ur.id = ura.role_id
            WHERE ura.user_id = %s
        """, (user_id,))
        user['roles'] = [row['name'] for row in cursor.fetchall()]
        
        # Get user permissions
        cursor.execute("""
            SELECT DISTINCT p.name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.id
            JOIN user_role_assignments ura ON ur.id = ura.role_id
            WHERE ura.user_id = %s
        """, (user_id,))
        user['permissions'] = [row['name'] for row in cursor.fetchall()]
        
        return user
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.put("/profile")
async def update_profile(
    profile_update: ProfileUpdate,
    payload: dict = Depends(allow_authenticated)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        update_fields = []
        params = []
        
        if profile_update.first_name is not None:
            update_fields.append("first_name = %s")
            params.append(profile_update.first_name)
        if profile_update.last_name is not None:
            update_fields.append("last_name = %s")
            params.append(profile_update.last_name)
        if profile_update.phone is not None:
            update_fields.append("phone = %s")
            params.append(profile_update.phone)
        if profile_update.country_id is not None:
            update_fields.append("country_id = %s")
            params.append(profile_update.country_id)
        if profile_update.preferred_currency is not None:
            update_fields.append("preferred_currency = %s")
            params.append(profile_update.preferred_currency)
        if profile_update.preferred_language is not None:
            update_fields.append("preferred_language = %s")
            params.append(profile_update.preferred_language)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, params)
        connection.commit()
        
        logger.info(f"Profile updated for user: {user_id}")
        return {"message": "Profile updated successfully"}
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    payload: dict = Depends(allow_authenticated)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get current password hash
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not PasswordSecurity.verify_password(password_change.current_password, user['password_hash']):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Validate new password strength
        is_valid, message = PasswordSecurity.validate_password_strength(password_change.new_password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Hash new password
        new_hashed_password = PasswordSecurity.hash_password(password_change.new_password)
        
        # Update password
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hashed_password, user_id))
        connection.commit()
        
        logger.info(f"Password changed for user: {user_id}")
        return {"message": "Password changed successfully"}
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    payload: dict = Depends(allow_authenticated)
):
    try:
        user_id = int(payload.get("sub"))
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1]
        filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = f"{config.upload_path}/users/{filename}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user avatar in database
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (filename, user_id))
        connection.commit()
        connection.close()
        
        logger.info(f"Avatar uploaded for user: {user_id}")
        return {"message": "Avatar uploaded successfully", "avatar_url": filename}
    except Exception as e:
        logger.error(f"Avatar upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")
    finally:
        await file.close()

@app.get("/addresses")
async def get_user_addresses(payload: dict = Depends(allow_authenticated)):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM user_addresses 
            WHERE user_id = %s 
            ORDER BY is_default DESC, created_at DESC
        """, (user_id,))
        
        addresses = cursor.fetchall()
        return addresses
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.post("/addresses")
async def create_address(
    address: AddressCreate,
    payload: dict = Depends(allow_authenticated)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # If this is set as default, remove default from other addresses
        if address.is_default:
            cursor.execute("""
                UPDATE user_addresses 
                SET is_default = 0 
                WHERE user_id = %s
            """, (user_id,))
        
        cursor.execute("""
            INSERT INTO user_addresses (
                user_id, address_type, full_name, phone, address_line1, 
                address_line2, landmark, city, state, country, postal_code, is_default
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, address.address_type, address.full_name, address.phone,
            address.address_line1, address.address_line2, address.landmark,
            address.city, address.state, address.country, address.postal_code, address.is_default
        ))
        
        address_id = cursor.lastrowid
        connection.commit()
        
        logger.info(f"Address created for user: {user_id}, address_id: {address_id}")
        return {"message": "Address created successfully", "address_id": address_id}
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.delete("/addresses/{address_id}")
async def delete_address(
    address_id: int = Path(..., gt=0),
    payload: dict = Depends(allow_authenticated)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            DELETE FROM user_addresses 
            WHERE id = %s AND user_id = %s
        """, (address_id, user_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Address not found")
        
        connection.commit()
        
        logger.info(f"Address deleted: {address_id} by user: {user_id}")
        return {"message": "Address deleted successfully"}
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('USER')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )
