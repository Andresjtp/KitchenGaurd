#!/usr/bin/env python3
"""
Migration helper script
Updates SQL queries from SQLite to PostgreSQL compatible syntax
"""

import re


def convert_sqlite_to_postgres_query(query):
    """Convert SQLite-specific syntax to PostgreSQL"""

    # Replace INTEGER PRIMARY KEY AUTOINCREMENT with SERIAL PRIMARY KEY
    query = re.sub(
        r"id\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        "id SERIAL PRIMARY KEY",
        query,
        flags=re.IGNORECASE,
    )

    # Replace TEXT with VARCHAR(255) for non-TEXT fields
    # (keep TEXT for large text fields)

    # Replace BOOLEAN DEFAULT 1 with BOOLEAN DEFAULT TRUE
    query = re.sub(
        r"BOOLEAN\s+DEFAULT\s+1", "BOOLEAN DEFAULT TRUE", query, flags=re.IGNORECASE
    )

    # Replace BOOLEAN DEFAULT 0 with BOOLEAN DEFAULT FALSE
    query = re.sub(
        r"BOOLEAN\s+DEFAULT\s+0", "BOOLEAN DEFAULT FALSE", query, flags=re.IGNORECASE
    )

    # Replace ? placeholders with %s
    # Count the number of ? and replace with numbered placeholders
    placeholder_count = query.count("?")
    for i in range(placeholder_count):
        query = query.replace("?", "%s", 1)

    return query


def get_placeholder(db_type="postgresql"):
    """Get the correct placeholder for the database"""
    return "%s" if db_type == "postgresql" else "?"


print("Migration helper loaded")
print(f"Use convert_sqlite_to_postgres_query(query) to convert queries")
print(f"Use get_placeholder(db_type) to get correct placeholder")
