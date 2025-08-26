"""
Enhanced Database Connection Manager with Connection Pooling

This module provides a centralized database connection manager with:
- Connection pooling for improved performance
- Automatic connection cleanup
- Better error handling and logging
- Connection health monitoring
"""

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional
import logging
from dotenv import load_dotenv
import threading
import time

load_dotenv(override=True)

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Centralized database connection manager with pooling"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure one connection pool per application"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the connection pool if not already done"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': os.getenv('POSTGRES_PORT', 5432),
            'database': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
        
        # Connection pool configuration
        self.min_connections = 1
        self.max_connections = 10
        self.connection_pool = None
        
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                **self.db_config
            )
            logger.info(f"Database connection pool initialized: {self.min_connections}-{self.max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool with automatic cleanup"""
        connection = None
        try:
            if self.connection_pool is None:
                raise RuntimeError("Connection pool not initialized")
            
            connection = self.connection_pool.getconn()
            if connection is None:
                raise RuntimeError("Could not get connection from pool")
            
            # Test connection health
            if connection.closed != 0:
                logger.warning("Retrieved closed connection, getting new one")
                self.connection_pool.putconn(connection, close=True)
                connection = self.connection_pool.getconn()
            
            yield connection
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                # Mark connection as bad and close it
                try:
                    connection.rollback()
                except:
                    pass
                self.connection_pool.putconn(connection, close=True)
                connection = None
            raise
        finally:
            if connection and not connection.closed:
                # Return healthy connection to pool
                self.connection_pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True):
        """Get a cursor with automatic connection and cursor cleanup"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            with conn.cursor(cursor_factory=cursor_factory) as cursor:
                yield conn, cursor
    
    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")
    
    def get_pool_status(self) -> dict:
        """Get current connection pool status"""
        if not self.connection_pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "closed": self.connection_pool.closed
        }


# Global instance
db_manager = DatabaseConnectionManager()


# Convenience function for backward compatibility
def get_connection():
    """Get a database connection (backward compatibility)"""
    return psycopg2.connect(**db_manager.db_config)


# Context manager for transactional operations
@contextmanager
def database_transaction():
    """Context manager for database transactions with automatic rollback on error"""
    with db_manager.get_connection() as conn:
        try:
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            conn.autocommit = True


# Enhanced connection context manager with retry logic
@contextmanager
def robust_database_connection(max_retries: int = 3, retry_delay: float = 1.0):
    """Database connection with retry logic for handling transient failures"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            with db_manager.get_connection() as conn:
                yield conn
                return
        except Exception as e:
            last_exception = e
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
            
    logger.error(f"All {max_retries} database connection attempts failed")
    raise last_exception


if __name__ == "__main__":
    # Test the connection manager
    try:
        print("Testing database connection manager...")
        
        with db_manager.get_cursor() as (conn, cursor):
            cursor.execute("SELECT version()")
            result = cursor.fetchone()
            print(f"✅ Database connection successful: {result}")
        
        pool_status = db_manager.get_pool_status()
        print(f"✅ Connection pool status: {pool_status}")
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
    finally:
        db_manager.close_all_connections()
