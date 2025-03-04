# app/main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional
from pydantic import BaseModel
from app.config import load_env_variables
from app.llm.llm_chain import generate_sql_query_with_llm, initialize_llm
from app.llm.vector_store import get_relevant_info, VECTOR_STORE_PATH, create_vector_store_from_files
from app.db_management.schema_loader import load_db_schema, SCHEMA_OUTPUT_DIR
from app.metadata_management.metadata_loader import process_metadata, METADATA_OUTPUT_FILE
from app.db_management.connection import (DatabaseConnection, get_postgres_connection, 
                                          get_databricks_connection, PostgresConnection, DatabricksConnection
                                           , SnowflakeConnection, get_snowflake_connection)
from app.db_management.schemas import (PostgresDBCredentials, DatabricksDBCredentials, 
                                       SnowflakeDBCredentials, ExecuteQueryRequest)
import os
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
env_vars = load_env_variables()
llm, embeddings = initialize_llm()
chat_history: List[Dict[str, str]] = []  # In-memory chat history


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/connect-postgres/")
async def connect_postgres(db_credentials: PostgresDBCredentials = Depends()): # Directly use PostgresDBCredentials
    """Endpoint to test PostgreSQL database connection."""
    try:
        db_connection: PostgresConnection = get_postgres_connection(db_credentials.dict()) # Get Postgres connection using factory
        if db_connection.test_connection():
            app.state.db_connection = db_connection
            app.state.db_type = "postgres" # Hardcode db_type here as it's postgres endpoint
            return {"message": "Database connection to Postgres successful"}
        else:
            raise HTTPException(status_code=400, detail="Database connection to Postgres failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Postgres database: {e}")

@app.post("/connect-snowflake/")
async def connect_snowflake(db_credentials: SnowflakeDBCredentials = Depends()): # Directly use SnowflakeDBCredentials
    """Endpoint to test Snowflake database connection."""
    try:
        db_connection: SnowflakeConnection = get_snowflake_connection(db_credentials.dict()) # Get Snowflake connection using factory
        if db_connection.test_connection():
            app.state.db_connection = db_connection
            app.state.db_type = "snowflake" # Hardcode db_type here as it's snowflake endpoint
            return {"message": "Database connection to Snowflake successful"}
        else:
            raise HTTPException(status_code=400, detail="Database connection to Snowflake failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Snowflake database: {e}")

@app.post("/connect-databricks/")
async def connect_databricks(db_credentials: DatabricksDBCredentials = Depends()): # Directly use DatabricksDBCredentials
    """Endpoint to test Databricks database connection."""
    try:
        db_connection: DatabricksConnection = get_databricks_connection(db_credentials.dict()) # Get Databricks connection using factory
        if db_connection.test_connection():
            app.state.db_connection = db_connection
            app.state.db_type = "databricks" # Hardcode db_type here as it's databricks endpoint
            return {"message": "Database connection to Databricks successful"}
        else:
            raise HTTPException(status_code=400, detail="Database connection to Databricks failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Database connection to Databricks failed")



@app.post("/load-schema/")
async def load_schema():
    """Endpoint to trigger schema loading from the database."""
    if not hasattr(app.state, 'db_connection'):
        raise HTTPException(status_code=400, detail="Database connection not established. Please connect to database first.")
    try:
        schema_data = load_db_schema(app.state.db_connection, app.state.db_type)
        app.state.schema_loaded = True
        return {"message": "Database schema loaded successfully", "schema_info": f"Schema documentation generated in '{os.path.join(SCHEMA_OUTPUT_DIR, 'schema.json')}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load database schema: {e}")


@app.post("/load-metadata/")
async def load_metadata():
    """Endpoint to trigger metadata loading from files."""
    try:
        metadata = process_metadata()
        app.state.metadata_loaded = True
        return {"message": "Metadata loaded successfully", "metadata_info": f"Metadata documentation generated in '{METADATA_OUTPUT_FILE}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load metadata: {e}")


@app.post("/create-vector-store/")
async def create_vector_store():
    """Endpoint to create vector store from schema and metadata files."""
    if not hasattr(app.state, 'schema_loaded'):
        raise HTTPException(status_code=400, detail="Database schema not loaded. Please load schema first.")
    if not hasattr(app.state, 'metadata_loaded'):
        raise HTTPException(status_code=400, detail="Metadata not loaded. Please load metadata first.")
    
    try:
        # Check if schema and metadata files exist
        schema_path = os.path.join(SCHEMA_OUTPUT_DIR, 'schema.json')
        if not os.path.exists(schema_path):
            raise HTTPException(status_code=400, detail="Schema file not found. Please load schema first.")
        if not os.path.exists(METADATA_OUTPUT_FILE):
            raise HTTPException(status_code=400, detail="Metadata file not found. Please load metadata first.")
        
        # Create vector store
        create_vector_store_from_files(
            schema_path=schema_path,
            metadata_path=METADATA_OUTPUT_FILE,
            persist_dir=VECTOR_STORE_PATH
        )
        
        return {"message": "Vector store created successfully", "path": VECTOR_STORE_PATH}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vector store: {str(e)}")


@app.post("/generate-query/")
async def generate_query(query_text: str):
    """Endpoint to generate SQL query using SSE for streaming."""
    global chat_history

    if not hasattr(app.state, 'db_connection'):
        raise HTTPException(status_code=400, detail="Database connection not established. Please connect to database first.")
    if not hasattr(app.state, 'schema_loaded'):
        raise HTTPException(status_code=400, detail="Database schema not loaded. Please load schema first.")

    async def event_stream():
        try:
            # Check if vector store exists
            if not os.path.exists(VECTOR_STORE_PATH) or not os.listdir(VECTOR_STORE_PATH):
                yield json.dumps({"event": "error", "data": "Vector store not found. Please call /create-vector-store/ endpoint first."})
                return

            # yield json.dumps({"event": "status", "data": "Analyzing schema..."})
            sql_query_explanation = generate_sql_query_with_llm(
                user_query=query_text,
                chat_history=chat_history,
                embeddings=embeddings,
                llm=llm,
                vector_store_path=VECTOR_STORE_PATH,
                db_type=app.state.db_type
            )
            # yield json.dumps({"event": "status", "data": "Generating SQL..."})
            yield json.dumps({"event": "sql_query", "data": sql_query_explanation})

            # Update chat history
            chat_history.extend([
                {"role": "user", "content": query_text},
                {"role": "assistant", "content": sql_query_explanation}
            ])

        except Exception as e:
            yield json.dumps({"event": "error", "data": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/execute-query/")
async def execute_query_endpoint(request_body: ExecuteQueryRequest):
    """Endpoint to execute SQL query."""
    if not hasattr(app.state, 'db_connection'):
        raise HTTPException(status_code=400, detail="Database connection not established. Please connect to database first.")

    sql_query = request_body.sql_query

    db_connection: DatabaseConnection = app.state.db_connection
    results, columns, error = db_connection.execute_query(sql_query)
    formatted_results = db_connection.format_results(results, columns, error)
    return {"results": formatted_results, "error": error}



# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)