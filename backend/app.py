"""
KitchenGuard Backend Application
Flask-based API for inventory management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Database configuration
DATABASE_PATH = "database.db"


def init_db():
    """Initialize the database with the products table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create products table as shown in Step 2
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            current_stock INTEGER DEFAULT 0,
            unit_cost REAL,
            supplier TEXT
        )
    """)

    conn.commit()
    conn.close()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "KitchenGuard API is running"})


@app.route("/inventory", methods=["GET"])
def get_inventory():
    """Get all products in inventory"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    # Convert to list of dictionaries
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
            }
        )

    conn.close()
    return jsonify(product_list)


@app.route("/inventory", methods=["POST"])
def add_product():
    """Add a new product to inventory"""
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

    return jsonify({"id": product_id, "message": "Product added successfully"}), 201


@app.route("/inventory/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Update product details or stock"""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check if product exists
    cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    if not cursor.fetchone():
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
            supplier = COALESCE(?, supplier)
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

    return jsonify({"message": "Product updated successfully"})


@app.route("/inventory/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Remove a product from inventory"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Check if product exists
    cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Product deleted successfully"})


if __name__ == "__main__":
    # Initialize database on startup
    init_db()

    # Run the Flask application
    app.run(debug=True, host="0.0.0.0", port=5000)
