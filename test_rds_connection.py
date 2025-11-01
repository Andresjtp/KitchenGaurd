#!/usr/bin/env python3
"""
Quick test script to verify RDS connection
"""

import psycopg2
import sys

print("Testing RDS Connection...")
print("=" * 60)

# Your RDS details
RDS_HOST = input("Enter RDS endpoint: ").strip()
RDS_PORT = input("Enter port (default 5432): ").strip() or "5432"
RDS_USER = input("Enter username: ").strip()
RDS_PASSWORD = input("Enter password: ").strip()
RDS_DATABASE = input("Enter database name (default postgres): ").strip() or "postgres"

print("\n" + "=" * 60)
print(f"Attempting to connect to:")
print(f"  Host: {RDS_HOST}")
print(f"  Port: {RDS_PORT}")
print(f"  Database: {RDS_DATABASE}")
print(f"  User: {RDS_USER}")
print("=" * 60 + "\n")

try:
    conn = psycopg2.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        database=RDS_DATABASE,
        user=RDS_USER,
        password=RDS_PASSWORD,
        connect_timeout=10,
    )

    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()

    print("✅ CONNECTION SUCCESSFUL!\n")
    print(f"PostgreSQL version: {version[0]}\n")

    # List existing databases
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    databases = cursor.fetchall()
    print("Existing databases:")
    for db in databases:
        print(f"  - {db[0]}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("✅ Connection test passed! You can now run the setup script.")
    print("=" * 60)

except psycopg2.OperationalError as e:
    print("❌ CONNECTION FAILED!")
    print(f"\nError: {e}\n")

    print("Common Issues & Solutions:")
    print("-" * 60)
    print("1. SECURITY GROUP:")
    print("   → Go to AWS Console → EC2 → Security Groups")
    print("   → Find the security group attached to your RDS")
    print("   → Add inbound rule: PostgreSQL (5432) from YOUR IP")
    print("   → Get your IP: https://whatismyipaddress.com")
    print()
    print("2. PUBLIC ACCESSIBILITY:")
    print("   → Go to AWS Console → RDS → Your Database")
    print("   → Check 'Connectivity & security' tab")
    print("   → 'Publicly accessible' should be 'Yes'")
    print("   → If 'No', modify the database to enable it")
    print()
    print("3. VPC & SUBNET:")
    print("   → Ensure RDS is in a public subnet")
    print("   → Check if Internet Gateway is attached to VPC")
    print()
    print("4. ENDPOINT & CREDENTIALS:")
    print("   → Double-check your RDS endpoint (no typos)")
    print("   → Verify username and password are correct")
    print("   → Default database is usually 'postgres'")
    print()
    print("5. NETWORK:")
    print("   → If on VPN, try disconnecting")
    print("   → Check firewall isn't blocking port 5432")
    print("-" * 60)
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
