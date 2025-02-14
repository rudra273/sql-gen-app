# app/db_management/schemas.py
from pydantic import BaseModel, Field

class PostgresDBCredentials(BaseModel):
    dbname: str = Field(..., description="Database name")
    user: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    host: str = Field(..., description="Database host")
    port: str = Field(..., description="Database port")

class DatabricksDBCredentials(BaseModel):
    server_hostname: str = Field(..., description="Databricks Server Hostname")
    http_path: str = Field(..., description="Databricks HTTP Path")
    access_token: str = Field(..., description="Databricks Access Token")