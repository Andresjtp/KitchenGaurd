"""
Authentication Service - PostgreSQL Version
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
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "kitchenguard_auth")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Service registry configuration
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
SERVICE_NAME = os.getenv("SERVICE_NAME", "auth-service")


def get_db_connection():
    """Get PostgreSQL database connection"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    return conn


def get_cursor(conn):
    """Get cursor with dictionary results"""
    return conn.cursor(cursor_factory=RealDictCursor)


def init_database():
    """Initialize the authentication database"""
    conn = get_db_connection()
    cursor = get_cursor(conn)

    # Create users table
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

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

    conn.commit()
    cursor.close()
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
    return len(password) >= 6


def generate_jwt_token(user_id, username):
    """Generate JWT token for authenticated user"""
    expiration = datetime.datetime.utcnow() + datetime.timedelta(
        hours=JWT_EXPIRATION_HOURS
    )

    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expiration,
        "iat": datetime.datetime.utcnow(),
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token


def authenticate():
    """Decorator for routes that require authentication"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get("Authorization")

            if not token:
                return jsonify({"error": "No token provided"}), 401

            if token.startswith("Bearer "):
                token = token[7:]

            try:
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
                # Store user info in request context if needed
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

        return decorated_function

    return decorator


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"service": SERVICE_NAME, "status": "healthy", "port": AUTH_PORT})


@app.route("/register", methods=["POST"])
def register():
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
            if field not in data or not data[field]:
                return jsonify({"error": f"{field} is required"}), 400

        username = data["username"].strip()
        email = data["email"].strip().lower()
        password = data["password"]
        full_name = data["fullName"].strip()
        restaurant_name = data["restaurantName"].strip()
        restaurant_type = data["restaurantType"].strip()
        user_position = data["userPosition"].strip()
        kitchen_produce_list = json.dumps(data.get("kitchenProduceList", []))
        bar_produce_list = json.dumps(data.get("barProduceList", []))

        # Validate email format
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate password strength
        if not validate_password(password):
            return jsonify(
                {"error": "Password must be at least 6 characters long"}
            ), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        # Check if username or email already exists
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s", (username, email)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Username or email already exists"}), 409

        # Hash the password
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Insert new user
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, full_name, restaurant_name, 
                             restaurant_type, user_position, kitchen_produce_list, bar_produce_list)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
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

        user_id = cursor.fetchone()["id"]
        conn.commit()
        cursor.close()
        conn.close()

        # Generate JWT token
        token = generate_jwt_token(user_id, username)

        # Send inventory data to inventory service in background
        if data.get("kitchenProduceList") or data.get("barProduceList"):

            def send_inventory_data():
                try:
                    # Send kitchen inventory
                    if data.get("kitchenProduceList"):
                        requests.post(
                            "http://localhost:8001/inventory/kitchen",
                            json={
                                "user_id": user_id,
                                "items": data["kitchenProduceList"],
                            },
                            timeout=2,
                        )
                        print(f"✅ Kitchen inventory sent for user {user_id}")

                    # Send bar inventory
                    if data.get("barProduceList"):
                        requests.post(
                            "http://localhost:8001/inventory/bar",
                            json={"user_id": user_id, "items": data["barProduceList"]},
                            timeout=2,
                        )
                        print(f"✅ Bar inventory sent for user {user_id}")
                except Exception as e:
                    print(f"⚠️ Error sending inventory data: {e}")

            # Start inventory import in background thread
            inventory_thread = threading.Thread(target=send_inventory_data)
            inventory_thread.daemon = True
            inventory_thread.start()

        return jsonify(
            {
                "message": "User registered successfully",
                "token": token,
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "fullName": full_name,
                    "restaurantName": restaurant_name,
                    "restaurantType": restaurant_type,
                    "userPosition": user_position,
                },
            }
        ), 201

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Username and password are required"}), 400

        username = data["username"].strip()
        password = data["password"]

        conn = get_db_connection()
        cursor = get_cursor(conn)

        # Get user by username
        cursor.execute(
            """
            SELECT id, username, email, password_hash, full_name, restaurant_name,
                   restaurant_type, user_position, is_active
            FROM users
            WHERE username = %s
        """,
            (username,),
        )

        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401

        # Check if account is active
        if not user["is_active"]:
            cursor.close()
            conn.close()
            return jsonify({"error": "Account is disabled"}), 403

        # Verify password
        if not bcrypt.checkpw(
            password.encode("utf-8"), user["password_hash"].encode("utf-8")
        ):
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401

        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
            (user["id"],),
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Generate JWT token
        token = generate_jwt_token(user["id"], user["username"])

        return jsonify(
            {
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "fullName": user["full_name"],
                    "restaurantName": user["restaurant_name"],
                    "restaurantType": user["restaurant_type"],
                    "userPosition": user["user_position"],
                },
            }
        ), 200

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500


@app.route("/reset-password", methods=["POST"])
def reset_password():
    """Initiate password reset process"""
    try:
        data = request.get_json()

        if not data or "email" not in data:
            return jsonify({"error": "Email is required"}), 400

        email = data["email"].strip().lower()

        conn = get_db_connection()
        cursor = get_cursor(conn)

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            # In production, generate token and send email
            # For now, just acknowledge the request
            print(f"Password reset requested for: {email}")

        cursor.close()
        conn.close()

        # Always return success to prevent email enumeration
        return jsonify(
            {
                "message": "If an account with that email exists, a password reset link has been sent"
            }
        ), 200

    except Exception as e:
        print(f"Password reset error: {str(e)}")
        return jsonify({"error": "Password reset failed"}), 500


if __name__ == "__main__":
    print("🔐 Starting Authentication Service...")
    init_database()

    # Register with API Gateway
    register_with_gateway()

    app.run(host="0.0.0.0", port=AUTH_PORT, debug=True)
