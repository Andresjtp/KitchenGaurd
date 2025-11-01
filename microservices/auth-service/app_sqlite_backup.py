"""
Authentication Service
Handles user registration, login, password reset, and session management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import jwt
import json
import datetime
import os
import re
import requests
import threading
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
AUTH_PORT = int(os.getenv("AUTH_PORT", 8007))
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "kitchenguard-secret-key-change-in-production"
)
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "postgresql")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "kitchenguard_auth")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Service registry configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
SERVICE_NAME = os.getenv("SERVICE_NAME", "auth-service")


def get_db_connection():
    """Get database connection based on DB_TYPE"""
    if DB_TYPE == "postgresql":
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        return conn
    else:
        # Fallback to SQLite for development
        import sqlite3

        conn = sqlite3.connect("auth_database.db")
        conn.row_factory = sqlite3.Row
        return conn


def get_cursor(conn):
    """Get appropriate cursor for database type"""
    if DB_TYPE == "postgresql":
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()


def init_database():
    """Initialize the authentication database"""
    conn = get_db_connection()
    cursor = get_cursor(conn)

    # Create users table with PostgreSQL-compatible syntax
    if DB_TYPE == "postgresql":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                restaurant_name VARCHAR(255) NOT NULL,
                restaurant_type VARCHAR(255),
                user_position VARCHAR(255),
                kitchen_produce_list TEXT,
                bar_produce_list TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP
            )
        """)

        # Create password reset tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
    else:
        # SQLite syntax
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                restaurant_name TEXT NOT NULL,
                restaurant_type TEXT,
                user_position TEXT,
                kitchen_produce_list TEXT,
                bar_produce_list TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                last_login TIMESTAMP
            )
        """)

        # Create password reset tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

    conn.commit()
    conn.close()
    print("✅ Authentication database initialized")


def register_with_gateway():
    """Register this service with the API Gateway"""
    try:
        service_info = {
            "name": SERVICE_NAME,
            "host": "localhost",
            "port": AUTH_PORT,
            "health_endpoint": f"http://localhost:{AUTH_PORT}/health",
            "endpoints": [
                {"path": "/register", "methods": ["POST"]},
                {"path": "/login", "methods": ["POST"]},
                {"path": "/reset-password", "methods": ["POST"]},
                {"path": "/health", "methods": ["GET"]},
            ],
        }

        response = requests.post(
            f"{API_GATEWAY_URL}/register", json=service_info, timeout=5
        )
        if response.status_code == 200:
            print(f"✅ {SERVICE_NAME} registered with API Gateway")
        else:
            print(f"⚠️ Failed to register with API Gateway: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not reach API Gateway: {e}")


def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Valid password"


def hash_password(password):
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
    return password_hash.decode("utf-8")


def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_jwt_token(user_id, username):
    """Generate JWT token for user"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token


def verify_jwt_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.current_user = payload
        return f(*args, **kwargs)

    return decorated_function


def token_required(f):
    """Decorator to require JWT token and pass user_id to function"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(payload["user_id"], *args, **kwargs)

    return decorated_function


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"service": "auth-service", "status": "healthy", "port": AUTH_PORT})


@app.route("/register", methods=["POST"])
def register_user():
    """Register a new user"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            "username",
            "email",
            "password",
            "fullName",
            "restaurantName",
            "restaurantType",
            "userPosition",
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        username = data["username"].strip()
        email = data["email"].strip().lower()
        password = data["password"]
        full_name = data["fullName"].strip()
        restaurant_name = data["restaurantName"].strip()
        restaurant_type = data["restaurantType"].strip()
        user_position = data["userPosition"].strip()

        # Optional inventory lists (convert to JSON strings)
        kitchen_produce_list = (
            json.dumps(data.get("kitchenProduceList", []))
            if data.get("kitchenProduceList")
            else ""
        )
        bar_produce_list = (
            json.dumps(data.get("barProduceList", []))
            if data.get("barProduceList")
            else ""
        )

        # Validate email format
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Check if username or email already exists
        conn = get_db_connection()
        existing_user = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
        ).fetchone()

        if existing_user:
            conn.close()
            return jsonify({"error": "Username or email already exists"}), 409

        # Hash password and create user
        password_hash = hash_password(password)

        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, full_name, restaurant_name, restaurant_type, user_position, kitchen_produce_list, bar_produce_list)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                username,
                email,
                password_hash,
                full_name,
                restaurant_name,
                restaurant_type,
                user_position,
                kitchen_produce_list,
                bar_produce_list,
            ),
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Generate JWT token first (for faster response)
        token = generate_jwt_token(user_id, username)

        # Send inventory data to inventory service asynchronously (non-blocking)
        if data.get("kitchenProduceList") or data.get("barProduceList"):
            import threading

            def send_inventory_data():
                try:
                    # Send kitchen inventory
                    if data.get("kitchenProduceList"):
                        kitchen_response = requests.post(
                            "http://localhost:8001/inventory/kitchen",
                            json={
                                "user_id": user_id,
                                "items": data["kitchenProduceList"],
                            },
                            timeout=3,
                        )
                        if kitchen_response.status_code == 201:
                            print(f"✅ Kitchen inventory imported for user {user_id}")
                        else:
                            print(
                                f"⚠️ Kitchen inventory import failed: {kitchen_response.status_code}"
                            )

                    # Send bar inventory
                    if data.get("barProduceList"):
                        bar_response = requests.post(
                            "http://localhost:8001/inventory/bar",
                            json={"user_id": user_id, "items": data["barProduceList"]},
                            timeout=3,
                        )
                        if bar_response.status_code == 201:
                            print(f"✅ Bar inventory imported for user {user_id}")
                        else:
                            print(
                                f"⚠️ Bar inventory import failed: {bar_response.status_code}"
                            )
                except requests.exceptions.RequestException as e:
                    print(
                        f"Warning: Failed to send inventory data to inventory service: {e}"
                    )

            # Start inventory import in background thread
            inventory_thread = threading.Thread(target=send_inventory_data)
            inventory_thread.daemon = True
            inventory_thread.start()

        return jsonify(
            {
                "message": "User registered successfully",
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "fullName": full_name,
                    "restaurantName": restaurant_name,
                    "restaurantType": restaurant_type,
                    "userPosition": user_position,
                },
                "token": token,
            }
        ), 201

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/login", methods=["POST"])
def login_user():
    """Login user"""
    try:
        data = request.get_json()

        if not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400

        username = data["username"].strip()
        password = data["password"]

        # Find user by username or email
        conn = get_db_connection()
        user = conn.execute(
            """
            SELECT id, username, email, password_hash, full_name, restaurant_name, restaurant_type, user_position, is_active
            FROM users 
            WHERE (username = ? OR email = ?) AND is_active = 1
        """,
            (username, username),
        ).fetchone()

        if not user or not verify_password(password, user["password_hash"]):
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401

        # Update last login timestamp
        conn.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user["id"],),
        )
        conn.commit()
        conn.close()

        # Generate JWT token
        token = generate_jwt_token(user["id"], user["username"])

        return jsonify(
            {
                "message": "Login successful",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "fullName": user["full_name"],
                    "restaurantName": user["restaurant_name"],
                    "restaurantType": user["restaurant_type"],
                    "userPosition": user["user_position"],
                },
                "token": token,
            }
        )

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500


@app.route("/reset-password", methods=["POST"])
def reset_password():
    """Request password reset"""
    try:
        data = request.get_json()

        if not data.get("email"):
            return jsonify({"error": "Email is required"}), 400

        email = data["email"].strip().lower()

        # Check if user exists
        conn = get_db_connection()
        user = conn.execute(
            "SELECT id, username, full_name FROM users WHERE email = ? AND is_active = 1",
            (email,),
        ).fetchone()

        if user:
            # Generate reset token (in a real implementation, you'd send an email)
            import secrets

            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

            conn.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """,
                (user["id"], reset_token, expires_at),
            )
            conn.commit()

            print(f"Password reset token for {email}: {reset_token}")

        conn.close()

        # Always return success to prevent email enumeration
        return jsonify(
            {
                "message": "If an account exists with this email, you will receive password reset instructions"
            }
        )

    except Exception as e:
        print(f"Password reset error: {str(e)}")
        return jsonify({"error": "Password reset failed"}), 500


@app.route("/verify-token", methods=["POST"])
def verify_token():
    """Verify JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"valid": False, "error": "No token provided"}), 400

        token = auth_header.split(" ")[1]
        payload = verify_jwt_token(token)

        if payload:
            return jsonify({"valid": True, "user_id": payload["user_id"]})
        else:
            return jsonify({"valid": False, "error": "Invalid or expired token"}), 401

    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return jsonify({"valid": False, "error": "Token verification failed"}), 500


@app.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user_id):
    """Get user profile"""
    try:
        conn = get_db_connection()
        user = conn.execute(
            """
            SELECT username, email, full_name, restaurant_name, restaurant_type, user_position, 
                   kitchen_produce_list, bar_produce_list, created_at
            FROM users WHERE id = ?
        """,
            (current_user_id,),
        ).fetchone()

        conn.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify(
            {
                "user": {
                    "id": current_user_id,
                    "username": user[0],
                    "email": user[1],
                    "fullName": user[2],
                    "restaurantName": user[3],
                    "restaurantType": user[4],
                    "userPosition": user[5],
                    "kitchenProduceList": user[6] or "",
                    "barProduceList": user[7] or "",
                    "createdAt": user[8],
                }
            }
        ), 200

    except Exception as e:
        print(f"Profile fetch error: {str(e)}")
        return jsonify({"error": "Failed to fetch profile"}), 500


@app.route("/update-inventory", methods=["POST"])
@token_required
def update_inventory(current_user_id):
    """Update user's inventory lists"""
    try:
        data = request.get_json()
        kitchen_produce_list = data.get("kitchenProduceList", "")
        bar_produce_list = data.get("barProduceList", "")

        conn = get_db_connection()
        conn.execute(
            """
            UPDATE users 
            SET kitchen_produce_list = ?, bar_produce_list = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (kitchen_produce_list, bar_produce_list, current_user_id),
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "Inventory lists updated successfully"}), 200

    except Exception as e:
        print(f"Inventory update error: {str(e)}")
        return jsonify({"error": "Failed to update inventory lists"}), 500


if __name__ == "__main__":
    print("🔐 Starting Authentication Service...")
    init_database()

    # Register with API Gateway
    register_with_gateway()

    app.run(host="0.0.0.0", port=AUTH_PORT, debug=True)
