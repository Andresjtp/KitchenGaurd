#!/usr/bin/env python3
"""
Script to create and initialize databases on AWS RDS PostgreSQL instance
Run this script to set up the KitchenGuard databases
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# RDS Connection Details
# Replace these with your actual RDS credentials
RDS_HOST = input(
    "Enter your RDS endpoint (e.g., kitchenguard-db.abc123.us-east-1.rds.amazonaws.com): "
).strip()
RDS_PORT = input("Enter RDS port (default 5432): ").strip() or "5432"
RDS_MASTER_USER = input("Enter master username: ").strip()
RDS_MASTER_PASSWORD = input("Enter master password: ").strip()
RDS_MASTER_DB = (
    input("Enter master database name (default postgres): ").strip() or "postgres"
)

print("\n" + "=" * 60)
print("Connecting to RDS Instance...")
print("=" * 60)

try:
    # Connect to the master database
    conn = psycopg2.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        database=RDS_MASTER_DB,
        user=RDS_MASTER_USER,
        password=RDS_MASTER_PASSWORD,
    )

    # Set connection to autocommit mode
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print("✅ Connected to RDS successfully!\n")

    # Create Auth Database
    print("Creating 'kitchenguard_auth' database...")
    try:
        cursor.execute("CREATE DATABASE kitchenguard_auth;")
        print("✅ Database 'kitchenguard_auth' created successfully!")
    except psycopg2.errors.DuplicateDatabase:
        print("⚠️  Database 'kitchenguard_auth' already exists")

    # Create Inventory Database
    print("\nCreating 'kitchenguard_inventory' database...")
    try:
        cursor.execute("CREATE DATABASE kitchenguard_inventory;")
        print("✅ Database 'kitchenguard_inventory' created successfully!")
    except psycopg2.errors.DuplicateDatabase:
        print("⚠️  Database 'kitchenguard_inventory' already exists")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("Setting up AUTH database schema...")
    print("=" * 60)

    # Connect to auth database and create tables
    auth_conn = psycopg2.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        database="kitchenguard_auth",
        user=RDS_MASTER_USER,
        password=RDS_MASTER_PASSWORD,
    )
    auth_cursor = auth_conn.cursor()

    # Create users table
    auth_cursor.execute("""
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
        );
    """)
    print("✅ Created 'users' table")

    # Create password reset tokens table
    auth_cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    """)
    print("✅ Created 'password_reset_tokens' table")

    # Create indexes for performance
    auth_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);"
    )
    auth_cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    auth_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reset_tokens_token ON password_reset_tokens(token);"
    )
    print("✅ Created indexes for auth database")

    auth_conn.commit()
    auth_cursor.close()
    auth_conn.close()

    print("\n" + "=" * 60)
    print("Setting up INVENTORY database schema...")
    print("=" * 60)

    # Connect to inventory database and create tables
    inv_conn = psycopg2.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        database="kitchenguard_inventory",
        user=RDS_MASTER_USER,
        password=RDS_MASTER_PASSWORD,
    )
    inv_cursor = inv_conn.cursor()

    # Create products table
    inv_cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(255),
            current_stock INTEGER DEFAULT 0,
            unit_cost DECIMAL(10, 2),
            supplier VARCHAR(255),
            unit VARCHAR(50) DEFAULT 'each',
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Created 'products' table")

    # Create kitchen_produce table
    inv_cursor.execute("""
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
        );
    """)
    print("✅ Created 'kitchen_produce' table")

    # Create bar_supplies table
    inv_cursor.execute("""
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
        );
    """)
    print("✅ Created 'bar_supplies' table")

    # Create indexes for performance
    inv_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id);"
    )
    inv_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_kitchen_user_id ON kitchen_produce(user_id);"
    )
    inv_cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_bar_user_id ON bar_supplies(user_id);"
    )
    print("✅ Created indexes for inventory database")

    inv_conn.commit()
    inv_cursor.close()
    inv_conn.close()

    print("\n" + "=" * 60)
    print("🎉 SUCCESS! All databases and tables created!")
    print("=" * 60)
    print("\n📋 Summary:")
    print(f"   RDS Host: {RDS_HOST}")
    print(f"   Port: {RDS_PORT}")
    print(f"   Databases created:")
    print(f"     1. kitchenguard_auth")
    print(f"        - users table")
    print(f"        - password_reset_tokens table")
    print(f"     2. kitchenguard_inventory")
    print(f"        - products table")
    print(f"        - kitchen_produce table")
    print(f"        - bar_supplies table")

    print("\n📝 Next Steps:")
    print("   1. Save your RDS credentials in .env files")
    print("   2. Update microservices to use PostgreSQL")
    print("   3. Test the connection from your application")

except psycopg2.OperationalError as e:
    print(f"\n❌ Connection Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Check your RDS endpoint is correct")
    print("  2. Verify security group allows connections from your IP")
    print(
        "  3. Ensure RDS instance is publicly accessible (if connecting from outside VPC)"
    )
    print("  4. Confirm username and password are correct")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
