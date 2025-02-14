# not using this currently

import psycopg2
from typing import Dict, Any, List, Tuple

def load_postgres_schema(db_credentials: Dict) -> Dict:
    """Loads schema information from a PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(**db_credentials)
        cursor = conn.cursor()

        tables = get_all_tables(cursor)
        schema_data = {
            "tables": [],
            "relationships": []
        }

        for table in tables:
            print(f"Processing table: {table}")
            columns = get_table_schema(table, cursor)
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
                    "character_maximum_length": col_info[4],
                    "numeric_precision": col_info[5],
                    "numeric_scale": col_info[6],
                    "key_type": col_info[7],
                    "foreign_table": col_info[8],
                    "foreign_column": col_info[9],
                    "details": format_schema_info(col_info)
                }
                table_entry["columns"].append(column_entry)

                if col_info[7] == 'FOREIGN KEY':
                    schema_data["relationships"].append({
                        "source": f"{table}.{col_info[0]}",
                        "references": f"{col_info[8]}.{col_info[9]}"
                    })
            schema_data["tables"].append(table_entry)

        cursor.close()
        return schema_data

    except Exception as e:
        raise Exception(f"Error loading PostgreSQL schema: {e}")
    finally:
        if conn:
            conn.close()


def get_all_tables(cursor: psycopg2.extensions.cursor) -> List[str]:
    """Get list of all tables in the public schema."""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE';
    """)
    return [table[0] for table in cursor.fetchall()]


def get_table_schema(table_name: str, cursor: psycopg2.extensions.cursor) -> List[Tuple[Any, ...]]:
    """Get detailed schema information for a specific table."""
    cursor.execute("""
        SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            CASE
                WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
                WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
                ELSE ''
            END as key_type,
            fk.foreign_table_name,
            fk.foreign_column_name
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku
                ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = %s
        ) pk ON c.column_name = pk.column_name
        LEFT JOIN (
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
        ) fk ON c.column_name = fk.column_name
        WHERE c.table_name = %s
        ORDER BY c.ordinal_position;
    """, (table_name, table_name, table_name))
    return cursor.fetchall()

def get_table_size(table_name: str, cursor: psycopg2.extensions.cursor) -> int:
    """Get the number of rows in a table."""
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    return cursor.fetchone()[0]

def format_schema_info(schema_info: Tuple[Any, ...]) -> str:
    """Format column information into a readable string."""
    (column_name, data_type, is_nullable, default, max_length,
     num_precision, num_scale, key_type, foreign_table, foreign_column) = schema_info

    parts = []
    parts.append(f"Type: {data_type}")

    if max_length:
        parts.append(f"Length: {max_length}")
    if num_precision is not None and data_type.startswith('numeric'):
        parts.append(f"Precision: {num_precision}, Scale: {num_scale}")

    parts.append("Nullable" if is_nullable == 'YES' else "Not Nullable")

    if default:
        parts.append(f"Default: {default}")

    if key_type:
        parts.append(key_type)
        if key_type == 'FOREIGN KEY':
            parts.append(f"References {foreign_table}({foreign_column})")

    return " | ".join(parts)