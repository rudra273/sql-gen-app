import snowflake.connector
from typing import Dict, Any, List, Tuple

def load_snowflake_schema(db_credentials: Dict) -> Dict:
    """Loads schema information from a Snowflake database."""
    conn = None
    try:
        conn = snowflake.connector.connect(**db_credentials)
        cursor = conn.cursor()

        tables = get_all_tables(cursor, db_credentials['database'], db_credentials['schema'])
        schema_data = {
            "tables": [],
            "relationships": []
        }

        for table in tables:
            print(f"Processing table: {table}")
            columns = get_table_schema(table, cursor, db_credentials['database'], db_credentials['schema'])
            row_count = get_table_size(table, cursor)

            table_entry = {
                "table": table,
                "row_count": row_count,
                "columns": []
            }

            for col_info in columns:
                column_entry = {
                    "column_name": col_info[0],
                    "data_type": col_info[1],
                    "is_nullable": col_info[2],
                    "default": col_info[3],
                    "character_maximum_length": None,
                    "numeric_precision": None,
                    "numeric_scale": None,
                    "key_type": col_info[4],
                    "foreign_table": None,
                    "foreign_column": None
                }
                table_entry["columns"].append(column_entry)

            schema_data["tables"].append(table_entry)

        return schema_data

    except Exception as e:
        raise Exception(f"Error loading Snowflake schema: {e}")
    finally:
        if conn:
            conn.close()

def get_all_tables(cursor, database: str, schema: str) -> List[str]:
    """Get list of all tables in the specified schema."""
    cursor.execute(f"""
        SELECT TABLE_NAME 
        FROM {database}.INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_TYPE = 'BASE TABLE';
    """)
    return [table[0] for table in cursor.fetchall()]

def get_table_schema(table_name: str, cursor, database: str, schema: str) -> List[Tuple]:
    """Get detailed schema information for a specific table."""
    cursor.execute(f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CASE 
                WHEN tc.constraint_type = 'PRIMARY KEY' THEN 'PRIMARY KEY'
                ELSE ''
            END as key_type
        FROM {database}.INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN {database}.INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc 
            ON c.TABLE_NAME = tc.TABLE_NAME 
            AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        WHERE c.TABLE_SCHEMA = '{schema}'
        AND c.TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION;
    """)
    return cursor.fetchall()

def get_table_size(table_name: str, cursor) -> int:
    """Get the number of rows in a table."""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]
    except:
        return 0