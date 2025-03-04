# app/db_management/schemas.py
from pydantic import BaseModel, Field

class PostgresDBCredentials(BaseModel):
    dbname: str = Field(..., description="Database name")
    user: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    host: str = Field(..., description="Database host")
    port: str = Field(..., description="Database port")

class DatabricksDBCredentials(BaseModel):
    pass

class SnowflakeDBCredentials(BaseModel):
    user: str = Field(..., description="Snowflake username")
    account: str = Field(..., description="Snowflake account")
    password: str = Field(..., description="Snowflake password")
    warehouse: str = Field(..., description="Snowflake warehouse")
    database: str = Field(..., description="Snowflake database")
    schema: str = Field(..., description="Snowflake schema")

class ExecuteQueryRequest(BaseModel):
    sql_query: str = Field(..., description="SQL query to execute")
