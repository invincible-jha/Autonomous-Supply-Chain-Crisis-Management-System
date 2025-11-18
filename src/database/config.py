"""
Database configuration.
"""
import os
from typing import Optional


class DatabaseConfig:
    """Database configuration settings."""

    def __init__(self):
        self.DATABASE_URL = os.getenv(
            'DATABASE_URL',
            'postgresql://supplychain:supplychain@localhost:5432/supply_chain_db'
        )

        # Connection pool settings
        self.POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '5'))
        self.MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))
        self.POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))

        # Query settings
        self.QUERY_TIMEOUT = int(os.getenv('DB_QUERY_TIMEOUT', '30'))

        # Development settings
        self.ECHO_SQL = os.getenv('DB_ECHO_SQL', 'false').lower() == 'true'

    def get_url(self) -> str:
        """Get database URL."""
        return self.DATABASE_URL

    def get_test_url(self) -> str:
        """Get test database URL."""
        test_url = os.getenv('TEST_DATABASE_URL')
        if test_url:
            return test_url

        # Create test DB URL from main URL
        if 'postgresql://' in self.DATABASE_URL:
            return self.DATABASE_URL.replace('/supply_chain_db', '/supply_chain_test_db')
        return 'postgresql://supplychain:supplychain@localhost:5432/supply_chain_test_db'


# Global config instance
config = DatabaseConfig()
