from fastapi import FastAPI, HTTPException
import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service")

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'pavitra_trading',
    'user': 'pavitra_user',
    'password': 'user123'
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "Auth Service is running!"}

@app.get("/health")
async def health():
    """Health check with proper database connection test"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "service": "auth",
            "users_count": user_count
        }
    except Error as e:
        logger.error(f"Health check - Database error: {e}")
        return {"status": "healthy", "database": "disconnected", "service": "auth"}

@app.post("/register")
async def register_user(email: str, password: str, first_name: str, last_name: str):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # For now, skip password hashing to test
        # hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Insert user
        cursor.execute(
            "INSERT INTO users (email, password_hash, first_name, last_name) VALUES (%s, %s, %s, %s)",
            (email, password, first_name, last_name)  # Store plain text for testing
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        return {"message": "User created", "user_id": user_id, "email": email}
        
    except Error as e:
        logger.error(f"DB error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        cursor.close()
        conn.close()

@app.get("/users")
async def get_users():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, first_name, last_name FROM users")
        users = cursor.fetchall()
        return {"users": users}
    except Error as e:
        logger.error(f"DB error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


@app.get("/test-db")
async def test_db():
    """Direct database test"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return {"database": "working", "user_count": result['count']}
    except Exception as e:
        return {"database": "failed", "error": str(e)}
