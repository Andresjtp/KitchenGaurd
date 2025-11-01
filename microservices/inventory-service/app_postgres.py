"""
Inventory Microservice - PostgreSQL Version
Handles all inventory-related operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "inventory-service")
SERVICE_PORT = int(os.getenv("INVENTORY_PORT", 8001))

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "kitchenguard_inventory")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Service registry
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")


def get_db_connection():
    """Get PostgreSQL database connection"""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    return conn


def get_cursor(conn):
    """Get cursor with dictionary results"""
    return conn.cursor(cursor_factory=RealDictCursor)


def init_db():
    """Initialize the inventory database"""
    conn = get_db_connection()
    cursor = get_cursor(conn)

    # Kitchen produce table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kitchen_produce (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(255),
            supplier VARCHAR(255),
            unit_cost DECIMAL(10, 2),
            unit VARCHAR(50) DEFAULT 'each',
            current_stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bar supplies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bar_supplies (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(255),
            supplier VARCHAR(255),
            unit_cost DECIMAL(10, 2),
            unit VARCHAR(50) DEFAULT 'each',
            current_stock INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for better performance
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_kitchen_user_id ON kitchen_produce(user_id);"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_bar_user_id ON bar_supplies(user_id);"
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Inventory database initialized")


def register_service():
    """Register this service with the API Gateway"""
    try:
        service_info = {
            "name": SERVICE_NAME,
            "host": "localhost",
            "port": SERVICE_PORT,
            "health_endpoint": f"http://localhost:{SERVICE_PORT}/health",
            "endpoints": [
                {"path": "/inventory/kitchen", "methods": ["GET", "POST"]},
                {"path": "/inventory/bar", "methods": ["GET", "POST"]},
                {
                    "path": "/inventory/kitchen/<id>",
                    "methods": ["GET", "PUT", "DELETE"],
                },
                {"path": "/inventory/bar/<id>", "methods": ["GET", "PUT", "DELETE"]},
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


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"service": SERVICE_NAME, "status": "healthy", "port": SERVICE_PORT})


# Kitchen Inventory Endpoints
@app.route("/inventory/kitchen", methods=["POST"])
def import_kitchen_inventory():
    """Import kitchen inventory from CSV data"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        items = data.get("items", [])

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if not items:
            return jsonify({"error": "No items to import"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        imported_count = 0
        for item in items:
            try:
                cursor.execute(
                    """
                    INSERT INTO kitchen_produce (user_id, name, category, supplier, unit_cost, unit, current_stock)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        user_id,
                        item.get("name", ""),
                        item.get("category", ""),
                        item.get("supplier", ""),
                        float(item.get("unit_cost", 0)),
                        item.get("unit", "each"),
                        int(item.get("current_stock", 0)),
                    ),
                )
                imported_count += 1
            except Exception as e:
                print(f"Error importing item {item.get('name')}: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(
            {
                "message": "Kitchen inventory imported successfully",
                "imported_count": imported_count,
            }
        ), 201

    except Exception as e:
        print(f"Kitchen inventory import error: {str(e)}")
        return jsonify({"error": "Failed to import kitchen inventory"}), 500


@app.route("/inventory/kitchen", methods=["GET"])
def get_kitchen_inventory():
    """Get kitchen inventory for a user"""
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            """
            SELECT id, name, category, supplier, unit_cost, unit, current_stock, created_at, updated_at
            FROM kitchen_produce
            WHERE user_id = %s
            ORDER BY name
        """,
            (user_id,),
        )

        items = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert to list of dicts
        inventory = [dict(row) for row in items]

        return jsonify(
            {"user_id": user_id, "items": inventory, "total_items": len(inventory)}
        ), 200

    except Exception as e:
        print(f"Get kitchen inventory error: {str(e)}")
        return jsonify({"error": "Failed to retrieve kitchen inventory"}), 500


@app.route("/inventory/kitchen/<int:item_id>", methods=["PUT"])
def update_kitchen_item(item_id):
    """Update a kitchen inventory item"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        if "name" in data:
            update_fields.append("name = %s")
            params.append(data["name"])
        if "category" in data:
            update_fields.append("category = %s")
            params.append(data["category"])
        if "supplier" in data:
            update_fields.append("supplier = %s")
            params.append(data["supplier"])
        if "unit_cost" in data:
            update_fields.append("unit_cost = %s")
            params.append(float(data["unit_cost"]))
        if "unit" in data:
            update_fields.append("unit = %s")
            params.append(data["unit"])
        if "current_stock" in data:
            update_fields.append("current_stock = %s")
            params.append(int(data["current_stock"]))

        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        params.extend([item_id, user_id])

        cursor.execute(
            f"""
            UPDATE kitchen_produce
            SET {", ".join(update_fields)}
            WHERE id = %s AND user_id = %s
        """,
            params,
        )

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Kitchen item updated successfully"}), 200

    except Exception as e:
        print(f"Update kitchen item error: {str(e)}")
        return jsonify({"error": "Failed to update kitchen item"}), 500


@app.route("/inventory/kitchen/<int:item_id>", methods=["DELETE"])
def delete_kitchen_item(item_id):
    """Delete a kitchen inventory item"""
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            "DELETE FROM kitchen_produce WHERE id = %s AND user_id = %s",
            (item_id, user_id),
        )

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Kitchen item deleted successfully"}), 200

    except Exception as e:
        print(f"Delete kitchen item error: {str(e)}")
        return jsonify({"error": "Failed to delete kitchen item"}), 500


# Bar Inventory Endpoints
@app.route("/inventory/bar", methods=["POST"])
def import_bar_inventory():
    """Import bar inventory from CSV data"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        items = data.get("items", [])

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if not items:
            return jsonify({"error": "No items to import"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        imported_count = 0
        for item in items:
            try:
                cursor.execute(
                    """
                    INSERT INTO bar_supplies (user_id, name, category, supplier, unit_cost, unit, current_stock)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        user_id,
                        item.get("name", ""),
                        item.get("category", ""),
                        item.get("supplier", ""),
                        float(item.get("unit_cost", 0)),
                        item.get("unit", "each"),
                        int(item.get("current_stock", 0)),
                    ),
                )
                imported_count += 1
            except Exception as e:
                print(f"Error importing item {item.get('name')}: {e}")

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(
            {
                "message": "Bar inventory imported successfully",
                "imported_count": imported_count,
            }
        ), 201

    except Exception as e:
        print(f"Bar inventory import error: {str(e)}")
        return jsonify({"error": "Failed to import bar inventory"}), 500


@app.route("/inventory/bar", methods=["GET"])
def get_bar_inventory():
    """Get bar inventory for a user"""
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            """
            SELECT id, name, category, supplier, unit_cost, unit, current_stock, created_at, updated_at
            FROM bar_supplies
            WHERE user_id = %s
            ORDER BY name
        """,
            (user_id,),
        )

        items = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert to list of dicts
        inventory = [dict(row) for row in items]

        return jsonify(
            {"user_id": user_id, "items": inventory, "total_items": len(inventory)}
        ), 200

    except Exception as e:
        print(f"Get bar inventory error: {str(e)}")
        return jsonify({"error": "Failed to retrieve bar inventory"}), 500


@app.route("/inventory/bar/<int:item_id>", methods=["PUT"])
def update_bar_item(item_id):
    """Update a bar inventory item"""
    try:
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        if "name" in data:
            update_fields.append("name = %s")
            params.append(data["name"])
        if "category" in data:
            update_fields.append("category = %s")
            params.append(data["category"])
        if "supplier" in data:
            update_fields.append("supplier = %s")
            params.append(data["supplier"])
        if "unit_cost" in data:
            update_fields.append("unit_cost = %s")
            params.append(float(data["unit_cost"]))
        if "unit" in data:
            update_fields.append("unit = %s")
            params.append(data["unit"])
        if "current_stock" in data:
            update_fields.append("current_stock = %s")
            params.append(int(data["current_stock"]))

        update_fields.append("updated_at = CURRENT_TIMESTAMP")

        params.extend([item_id, user_id])

        cursor.execute(
            f"""
            UPDATE bar_supplies
            SET {", ".join(update_fields)}
            WHERE id = %s AND user_id = %s
        """,
            params,
        )

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Bar item updated successfully"}), 200

    except Exception as e:
        print(f"Update bar item error: {str(e)}")
        return jsonify({"error": "Failed to update bar item"}), 500


@app.route("/inventory/bar/<int:item_id>", methods=["DELETE"])
def delete_bar_item(item_id):
    """Delete a bar inventory item"""
    try:
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id parameter is required"}), 400

        conn = get_db_connection()
        cursor = get_cursor(conn)

        cursor.execute(
            "DELETE FROM bar_supplies WHERE id = %s AND user_id = %s",
            (item_id, user_id),
        )

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"error": "Item not found"}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Bar item deleted successfully"}), 200

    except Exception as e:
        print(f"Delete bar item error: {str(e)}")
        return jsonify({"error": "Failed to delete bar item"}), 500


if __name__ == "__main__":
    print("📦 Starting Inventory Service...")
    init_db()

    # Register with API Gateway
    register_service()

    app.run(host="0.0.0.0", port=SERVICE_PORT, debug=True)
