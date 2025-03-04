# app/db_management/schema_loader.py
import os
import json
from typing import Dict, Any, List, Tuple
from app.db_management.connection import DatabaseConnection, PostgresConnection, DatabricksConnection, SnowflakeConnection
from app.db_management.postgres_schema_loader import load_postgres_schema 
from app.db_management.databricks_schema_loader import load_databricks_schema 
from app.db_management.snowflake_schema_loader import load_snowflake_schema


path = os.path.dirname(os.path.abspath(__file__))

SCHEMA_OUTPUT_DIR = f'{path}/schema' 

def load_db_schema(db_connection: DatabaseConnection, db_type: str) -> Dict:
    """
    Loads schema information from the database based on db_type.
    Dispatches to database-specific schema loaders.
    Now uses the provided DatabaseConnection object.
    """
    output_dir = SCHEMA_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    db_type_lower = db_type.lower()

    if db_type_lower == 'postgres':
        if isinstance(db_connection, PostgresConnection): 
            schema_data = load_postgres_schema(db_connection.db_credentials) # Call postgres schema loader
        else:
            raise ValueError("Invalid DatabaseConnection object for PostgreSQL.") 
    elif db_type_lower == 'databricks':
        if isinstance(db_connection, DatabricksConnection):
            schema_data = load_databricks_schema(db_connection.db_credentials) # Call databricks schema loader (placeholder for now)
        else:
             raise ValueError("Invalid DatabaseConnection object for Databricks.") # Type mismatch error
    elif db_type_lower == 'snowflake':
        if isinstance(db_connection, SnowflakeConnection):
            schema_data = load_snowflake_schema(db_connection.db_credentials) # Call snowflake schema loader (placeholder for now)
        else:
             raise ValueError("Invalid DatabaseConnection object for Snowflake.") # Type mismatch error
    else:
        raise ValueError(f"Schema loading not implemented for database type: {db_type}")

    output_file = os.path.join(output_dir, 'schema.json')
    with open(output_file, 'w') as f:
        json.dump(schema_data, f, indent=4)

    print(f"Schema documentation generated in '{output_file}'")
    return schema_data


# You can potentially move format_schema_info, SCHEMA_OUTPUT_DIR etc., to a more common place
# if they are intended to be shared across schema loaders (though currently format_schema_info is PostgreSQL specific)