"""
Inventory Microservice
Handles all inventory-related operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests
import os

app = Flask(__name__)
CORS(app)

# Service configuration
SERVICE_NAME = "inventory-service"
SERVICE_PORT = 8001
DATABASE_PATH = "inventory.db"

# Service registry (for service discovery)
API_GATEWAY_URL = "http://localhost:8000"


def init_db():
    """Initialize the inventory database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            current_stock INTEGER DEFAULT 0,
            unit_cost REAL,
            supplier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def register_service():
    """Register this service with the API Gateway"""
    try:
        service_info = {
            "name": SERVICE_NAME,
            "host": "localhost",
            "port": SERVICE_PORT,
            "health_endpoint": f"http://localhost:{SERVICE_PORT}/health",
            "endpoints": [
                {"path": "/inventory", "methods": ["GET", "POST"]},
                {"path": "/inventory/<id>", "methods": ["GET", "PUT", "DELETE"]},
                {"path": "/inventory/low-stock", "methods": ["GET"]},
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


@app.route("/inventory", methods=["GET"])
def get_inventory():
    """Get all products in inventory"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products ORDER BY name")
        products = cursor.fetchall()

        product_list = []
        for product in products:
            product_list.append(
                {
                    "id": product[0],
                    "name": product[1],
                    "category": product[2],
                    "current_stock": product[3],
                    "unit_cost": product[4],
                    "supplier": product[5],
                    "created_at": product[6],
                    "updated_at": product[7],
                }
            )

        conn.close()

        # Publish event for analytics
        publish_event("inventory_viewed", {"count": len(product_list)})

        return jsonify(product_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/inventory", methods=["POST"])
def add_product():
    """Add a new product to inventory"""
    try:
        data = request.get_json()

        if not data or "name" not in data:
            return jsonify({"error": "Product name is required"}), 400

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO products (name, category, current_stock, unit_cost, supplier)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                data["name"],
                data.get("category", ""),
                data.get("current_stock", 0),
                data.get("unit_cost", 0.0),
                data.get("supplier", ""),
            ),
        )

        conn.commit()
        product_id = cursor.lastrowid
        conn.close()

        # Publish event for analytics and notifications
        publish_event(
            "product_added",
            {
                "product_id": product_id,
                "name": data["name"],
                "stock": data.get("current_stock", 0),
            },
        )

        return jsonify({"id": product_id, "message": "Product added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/inventory/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Update product details or stock"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Check if product exists
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        existing_product = cursor.fetchone()
        if not existing_product:
            conn.close()
            return jsonify({"error": "Product not found"}), 404

        # Update product
        cursor.execute(
            """
            UPDATE products 
            SET name = COALESCE(?, name),
                category = COALESCE(?, category),
                current_stock = COALESCE(?, current_stock),
                unit_cost = COALESCE(?, unit_cost),
                supplier = COALESCE(?, supplier),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (
                data.get("name"),
                data.get("category"),
                data.get("current_stock"),
                data.get("unit_cost"),
                data.get("supplier"),
                product_id,
            ),
        )

        conn.commit()
        conn.close()

        # Check for low stock and publish events
        new_stock = data.get("current_stock")
        if new_stock is not None and new_stock < 10:  # Low stock threshold
            publish_event(
                "low_stock_alert",
                {
                    "product_id": product_id,
                    "name": existing_product[1],
                    "current_stock": new_stock,
                },
            )

        publish_event("product_updated", {"product_id": product_id})

        return jsonify({"message": "Product updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/inventory/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Remove a product from inventory"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Check if product exists and get details
        cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            conn.close()
            return jsonify({"error": "Product not found"}), 404

        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()

        # Publish event
        publish_event("product_deleted", {"product_id": product_id, "name": product[0]})

        return jsonify({"message": "Product deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/inventory/low-stock", methods=["GET"])
def get_low_stock():
    """Get products with low stock levels"""
    try:
        threshold = request.args.get("threshold", 10, type=int)

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM products WHERE current_stock < ? ORDER BY current_stock",
            (threshold,),
        )
        products = cursor.fetchall()

        low_stock_products = []
        for product in products:
            low_stock_products.append(
                {
                    "id": product[0],
                    "name": product[1],
                    "category": product[2],
                    "current_stock": product[3],
                    "unit_cost": product[4],
                    "supplier": product[5],
                }
            )

        conn.close()
        return jsonify(low_stock_products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def publish_event(event_type, data):
    """Publish events to other services (simplified event bus)"""
    try:
        event_payload = {
            "event_type": event_type,
            "service": SERVICE_NAME,
            "data": data,
            "timestamp": "2025-10-01T00:00:00Z",  # In real app, use datetime.utcnow()
        }

        # Send to notification service
        requests.post("http://localhost:8005/events", json=event_payload, timeout=2)

        # Send to analytics service
        requests.post("http://localhost:8006/events", json=event_payload, timeout=2)

    except requests.exceptions.RequestException:
        # In production, you'd use a message queue like RabbitMQ or Kafka
        # For now, we'll just ignore failed event publishing
        pass


if __name__ == "__main__":
    print(f"🚀 Starting {SERVICE_NAME} on port {SERVICE_PORT}")

    # Initialize database
    init_db()

    # Register with API Gateway
    register_service()

    # Start the service
    app.run(debug=True, host="0.0.0.0", port=SERVICE_PORT)
