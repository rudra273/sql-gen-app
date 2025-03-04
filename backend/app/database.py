# import psycopg2
# from typing import Tuple, List, Optional, Dict

# def test_db_connection(db_credentials: Dict) -> bool:
#     """Test database connection using provided credentials."""
#     conn = None
#     try:
#         conn = psycopg2.connect(**db_credentials)
#         cursor = conn.cursor()
#         cursor.execute("SELECT 1;")
#         cursor.fetchone()
#         return True
#     except Exception as e:
#         print(f"Database connection failed: {e}")
#         return False
#     finally:
#         if conn:
#             conn.close()


# def execute_sql_query(query: str, db_credentials: Dict) -> Tuple[List, Optional[List[str]], Optional[str]]:
#     """Execute SQL query against PostgreSQL"""
#     conn = None
#     try:
#         conn = psycopg2.connect(**db_credentials)
#         cursor = conn.cursor()
#         cursor.execute(query)
#         results = cursor.fetchall()
#         column_names = [desc[0] for desc in cursor.description]
#         return results, column_names, None
#     except Exception as e:
#         return [], None, str(e)
#     finally:
#         if conn:
#             conn.close()


# def format_results(results: List, columns: Optional[List[str]], error: Optional[str]) -> str:
#     """Format query results for display"""
#     if error:
#         return f"Error: {error}"

#     if not results:
#         return "No results found."

#     output = []
#     if columns:
#         output.append(" | ".join(columns))
#         output.append("-" * len(output[0]))

#     for row in results[:50]:
#         output.append(" | ".join(str(value) for value in row))

#     if len(results) > 50:
#         output.append(f"\n... and {len(results) - 50} more rows")

#     return "\n".join(output)

