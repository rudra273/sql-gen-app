# app/db_management/connection.py
import psycopg2
from typing import Tuple, List, Optional, Dict, Type
from abc import ABC, abstractmethod
# from databricks import sql # Import Databricks SQL Connector if used
sql = None # Placeholder
import snowflake.connector

class DatabaseConnection(ABC):
    """Abstract base class for database connections."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Test database connection."""
        pass

    @abstractmethod
    def execute_query(self, query: str) -> Tuple[List, Optional[List[str]], Optional[str]]:
        """Execute SQL query."""
        pass

    @abstractmethod
    def format_results(self, results: List, columns: Optional[List[str]], error: Optional[str]) -> str:
        """Format query results for display."""
        pass


class PostgresConnection(DatabaseConnection):
    """Concrete class for PostgreSQL database connections."""
    def __init__(self, db_credentials: Dict):
        self.db_credentials = db_credentials

    def test_connection(self) -> bool:
        """Test PostgreSQL database connection."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_credentials)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            return True
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str) -> Tuple[List, Optional[List[str]], Optional[str]]:
        """Execute SQL query against PostgreSQL."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_credentials)
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            return results, column_names, None
        except Exception as e:
            return [], None, str(e)
        finally:
            if conn:
                conn.close()

    def format_results(self, results: List, columns: Optional[List[str]], error: Optional[str]) -> str:
        """Format query results for PostgreSQL (and standard SQL)."""
        if error:
            return f"Error: {error}"

        if not results:
            return "No results found."

        output = []
        if columns:
            output.append(" | ".join(columns))
            output.append("-" * len(output[0]))

        for row in results[:50]:
            output.append(" | ".join(str(value) for value in row))

        if len(results) > 50:
            output.append(f"\n... and {len(results) - 50} more rows")

        return "\n".join(output)


class DatabricksConnection(DatabaseConnection):
    """Concrete class for Databricks database connections."""

    def __init__(self, db_credentials: Dict):
        self.db_credentials = db_credentials

    def test_connection(self) -> bool:
        """Test Databricks database connection."""
        conn = None
        try:
            # from databricks import sql # Import here, only when DatabricksConnection is used
            conn = sql.connect(
                server_hostname=self.db_credentials['server_hostname'],
                http_path=self.db_credentials['http_path'],
                token=self.db_credentials['access_token']
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            return True
        except Exception as e:
            print(f"Databricks connection failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str) -> Tuple[List, Optional[List[str]], Optional[str]]:
        """Execute SQL query against Databricks."""
        conn = None
        try:
            # from databricks import sql # Import here, only when DatabricksConnection is used
            conn = sql.connect(
                server_hostname=self.db_credentials['server_hostname'],
                http_path=self.db_credentials['http_path'],
                token=self.db_credentials['access_token']
            )
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            return results, column_names, None
        except Exception as e:
            return [], None, str(e)
        finally:
            if conn:
                conn.close()

    def format_results(self, results: List, columns: Optional[List[str]], error: Optional[str]) -> str:
        """Format query results for Databricks."""
        if error:
            return f"Error: {error}"

        if not results:
            return "No results found."

        output = []
        if columns:
            output.append(" | ".join(columns))
            output.append("-" * len(output[0]))

        for row in results[:50]: # Limiting to 50 rows for display
            row_str_values = []
            for value in row:
                row_str_values.append(str(value)) # Explicitly convert each value to string
            output.append(" | ".join(row_str_values))


        if len(results) > 50:
            output.append(f"\n... and {len(results) - 50} more rows")

        return "\n".join(output)


class SnowflakeConnection(DatabaseConnection):
    """Concrete class for Snowflake database connections."""
    def __init__(self, db_credentials: Dict):
        self.db_credentials = db_credentials

    def test_connection(self) -> bool:
        """Test Snowflake database connection."""
        conn = None
        try:
            conn = snowflake.connector.connect(**self.db_credentials)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            return True
        except Exception as e:
            print(f"Snowflake connection failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str) -> Tuple[List, Optional[List[str]], Optional[str]]:
        """Execute SQL query against Snowflake."""
        conn = None
        try:
            conn = snowflake.connector.connect(**self.db_credentials)
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            return results, column_names, None
        except Exception as e:
            return [], None, str(e)
        finally:
            if conn:
                conn.close()

    def format_results(self, results: List, columns: Optional[List[str]], error: Optional[str]) -> str:
        """Format query results for Snowflake (and standard SQL)."""
        if error:
            return f"Error: {error}"

        if not results:
            return "No results found."

        output = []
        if columns:
            output.append(" | ".join(columns))
            output.append("-" * len(output[0]))

        for row in results[:50]:
            output.append(" | ".join(str(value) for value in row))

        if len(results) > 50:
            output.append(f"\n... and {len(results) - 50} more rows")

        return "\n".join(output)

# Simplified factory functions - directly return connection objects
def get_postgres_connection(db_credentials: Dict) -> PostgresConnection:
    """Factory function to get a PostgreSQL connection object."""
    return PostgresConnection(db_credentials)

def get_databricks_connection(db_credentials: Dict) -> DatabricksConnection:
    """Factory function to get a Databricks connection object."""
    return DatabricksConnection(db_credentials)

def get_snowflake_connection(db_credentials: Dict) -> SnowflakeConnection:
    """Factory function to get a Snowflake connection object."""
    return SnowflakeConnection(db_credentials)
