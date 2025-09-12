#!/usr/bin/env python3
"""
Database Configuration Module
Handles secure database credentials using environment variables.
"""

import os
from typing import Dict, Optional

class DatabaseConfig:
    """Secure database configuration using environment variables."""
    
    def __init__(self):
        """Initialize database configuration from environment variables."""
        self._postgres_config = self._get_postgres_config()
        self._mysql_config = self._get_mysql_config()
    
    def _get_postgres_config(self) -> Dict[str, str]:
        """Get PostgreSQL configuration from environment variables."""
        config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'postgres')
        }
        config['connection_string'] = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        return config
    
    def _get_mysql_config(self) -> Dict[str, str]:
        """Get MySQL configuration from environment variables."""
        config = {
            'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
            'port': os.getenv('MYSQL_PORT', '3306'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', 'mysql'),
            'database': os.getenv('MYSQL_DB', 'test')
        }
        config['connection_string'] = f"mysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        return config
    
    
    def get_postgres_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return self._postgres_config['connection_string']
    
    def get_mysql_connection_string(self) -> str:
        """Get MySQL connection string."""
        return self._mysql_config['connection_string']
    
    def get_historical_postgres_connection_string(self, historical_db_name: str) -> str:
        """Build a PostgreSQL connection string targeting the historical DB.

        Uses the same host/port/password as the base config. If the detected user
        name erroneously matches the database name (e.g., 'performance_history'),
        default to 'postgres' to avoid auth failures in common local setups.
        Allows optional overrides via HISTORICAL_POSTGRES_USER/PASSWORD.
        """
        base = self._postgres_config
        user = os.getenv('HISTORICAL_POSTGRES_USER', base['user'])
        # Avoid misconfigured environments where POSTGRES_USER == historical DB name
        if user == historical_db_name:
            user = 'postgres'
        password = os.getenv('HISTORICAL_POSTGRES_PASSWORD', base['password'])
        host = base['host']
        port = base['port']
        return f"postgresql://{user}:{password}@{host}:{port}/{historical_db_name}"
    
    def get_postgres_config(self) -> Dict[str, str]:
        """Get PostgreSQL configuration dictionary."""
        return self._postgres_config.copy()
    
    def get_mysql_config(self) -> Dict[str, str]:
        """Get MySQL configuration dictionary."""
        return self._mysql_config.copy()
    
    def validate_credentials(self) -> Dict[str, bool]:
        """Validate that required credentials are available."""
        validation = {
            'postgres': True,
            'mysql': True
        }
        
        # Check PostgreSQL credentials
        if not self._postgres_config['password']:
            validation['postgres'] = False
        
        # Check MySQL credentials  
        if not self._mysql_config['password']:
            validation['mysql'] = False
            
        return validation
    
    def print_config_status(self):
        """Print configuration status (without passwords)."""
        print("🔧 Database Configuration Status:")
        print(f"  PostgreSQL: {self._postgres_config['user']}@{self._postgres_config['host']}:{self._postgres_config['port']}/{self._postgres_config['database']}")
        print(f"  MySQL: {self._mysql_config['user']}@{self._mysql_config['host']}:{self._mysql_config['port']}/{self._mysql_config['database']}")
        
        validation = self.validate_credentials()
        if not validation['postgres']:
            print("  ⚠️  PostgreSQL password not set in environment")
        if not validation['mysql']:
            print("  ⚠️  MySQL password not set in environment")

# Global configuration instance
db_config = DatabaseConfig()

def get_database_config() -> DatabaseConfig:
    """Get the global database configuration instance."""
    return db_config

def get_postgres_connection_string() -> str:
    """Convenience function to get PostgreSQL connection string."""
    return db_config.get_postgres_connection_string()

def get_mysql_connection_string() -> str:
    """Convenience function to get MySQL connection string."""
    return db_config.get_mysql_connection_string()

def get_historical_postgres_connection_string(historical_db_name: str) -> str:
    """Convenience function to get historical PostgreSQL connection string."""
    return db_config.get_historical_postgres_connection_string(historical_db_name)

def get_postgres_config() -> Dict[str, str]:
    """Convenience function to get PostgreSQL configuration."""
    return db_config.get_postgres_config()

def get_mysql_config() -> Dict[str, str]:
    """Convenience function to get MySQL configuration."""
    return db_config.get_mysql_config()
