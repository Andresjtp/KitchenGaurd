"""
Database utility module for connecting to PostgreSQL or SQLite
Provides database connection management with environment variable support
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv()


class DatabaseConnection:
    """Manages database connections for both PostgreSQL and SQLite"""

    def __init__(self, db_type=None, db_name=None):
        """
        Initialize database connection manager

        Args:
            db_type: 'postgresql' or 'sqlite' (defaults to env var DB_TYPE)
            db_name: Database name (defaults to env var DB_NAME for PostgreSQL,
                     or provided name for SQLite)
        """
        self.db_type = db_type or os.getenv("DB_TYPE", "sqlite")

        if self.db_type == "postgresql":
            self.db_config = {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 5432)),
                "database": db_name or os.getenv("DB_NAME"),
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
            }
        else:
            # SQLite fallback
            self.db_name = db_name or "local_database.db"

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Automatically handles connection closing

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
        """
        if self.db_type == "postgresql":
            conn = psycopg2.connect(**self.db_config)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_name)
            try:
                yield conn
            finally:
                conn.close()

    def get_cursor(self, conn):
        """
        Get appropriate cursor for the database type

        Args:
            conn: Database connection object

        Returns:
            Database cursor
        """
        if self.db_type == "postgresql":
            return conn.cursor(cursor_factory=RealDictCursor)
        else:
            conn.row_factory = sqlite3.Row
            return conn.cursor()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """
        Execute a query and return results

        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetch_one: Return single row
            fetch_all: Return all rows

        Returns:
            Query results or None
        """
        with self.get_connection() as conn:
            cursor = self.get_cursor(conn)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cursor.lastrowid if self.db_type == "sqlite" else cursor.rowcount

    def format_placeholder(self, position=None):
        """
        Get the correct placeholder for parameterized queries

        PostgreSQL uses %s, SQLite uses ?

        Args:
            position: Position number (only used for PostgreSQL)

        Returns:
            Placeholder string
        """
        return "%s" if self.db_type == "postgresql" else "?"

    def get_last_insert_id(self, cursor):
        """
        Get the ID of the last inserted row

        Args:
            cursor: Database cursor

        Returns:
            Last insert ID
        """
        if self.db_type == "postgresql":
            cursor.execute("SELECT lastval()")
            return cursor.fetchone()[0]
        else:
            return cursor.lastrowid


# Convenience function to create database connection
def get_db(db_type=None, db_name=None):
    """
    Factory function to create database connection

    Args:
        db_type: 'postgresql' or 'sqlite'
        db_name: Database name

    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection(db_type=db_type, db_name=db_name)
