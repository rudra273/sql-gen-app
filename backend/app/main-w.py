from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Union
from pydantic import BaseModel
from app.config import load_env_variables
from app.database import test_db_connection, execute_sql_query, format_results
from app.llm.llm_chain import generate_sql_query_with_llm, initialize_llm
from app.llm.vector_store import get_relevant_info, VECTOR_STORE_PATH, create_vector_store_from_files
from app.db_management.schema_loader import load_db_schema, SCHEMA_OUTPUT_DIR
from app.metadata_management.metadata_loader import process_metadata, METADATA_OUTPUT_FILE
import os
import json


app = FastAPI()
env_vars = load_env_variables()
llm, embeddings = initialize_llm()
chat_history: List[Dict[str, str]] = [] # In-memory chat history


class DBCredentials(BaseModel):
    dbname: str
    user: str
    password: str
    host: str
    port: str

db_credentials_dep = Depends(DBCredentials)

@app.post("/connect-db/")
async def connect_db(db_credentials: DBCredentials):
    """Endpoint to test database connection."""
    db_dict = db_credentials.dict()
    if test_db_connection(db_dict):
        app.state.db_credentials = db_dict
        return {"message": "Database connection successful"}
    else:
        raise HTTPException(status_code=400, detail="Database connection failed")

@app.post("/load-schema/")
async def load_schema():
    """Endpoint to trigger schema loading from the database."""
    if not hasattr(app.state, 'db_credentials'):
        raise HTTPException(status_code=400, detail="Database credentials not provided. Please connect to database first.")
    try:
        schema_data = load_db_schema(app.state.db_credentials) 
        app.state.schema_loaded = True # Set flag to indicate schema is loaded
        return {"message": "Database schema loaded successfully", "schema_info": f"Schema documentation generated in '{os.path.join(SCHEMA_OUTPUT_DIR, 'schema.json')}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load database schema: {e}")



@app.post("/load-metadata/")
async def load_metadata():
    """Endpoint to trigger metadata loading from files."""
    try:
        metadata = process_metadata() 
        app.state.metadata_loaded = True # Set flag for metadata loaded
        return {"message": "Metadata loaded successfully", "metadata_info": f"Metadata documentation generated in '{METADATA_OUTPUT_FILE}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load metadata: {e}")


@app.post("/generate-query/")
async def generate_query(query_text: str):
    """Endpoint to generate SQL query using SSE for streaming, with dynamic vector store check."""
    global chat_history

    if not hasattr(app.state, 'db_credentials'):
        raise HTTPException(status_code=400, detail="Database credentials not provided. Please connect to database first.")
    if not hasattr(app.state, 'schema_loaded'):
        raise HTTPException(status_code=400, detail="Database schema not loaded. Please load schema first.")

    async def event_stream():
        try:
            # Check if vector store exists, create if not
            if not os.path.exists(VECTOR_STORE_PATH) or not os.listdir(VECTOR_STORE_PATH):
                yield json.dumps({"event": "status", "data": "Vector store not found. Creating..."})
                try:
                    create_vector_store_from_files(
                        schema_path=os.path.join(SCHEMA_OUTPUT_DIR, 'schema.json'),
                        metadata_path=METADATA_OUTPUT_FILE,
                        persist_dir=VECTOR_STORE_PATH
                    )
                    yield json.dumps({"event": "status", "data": "Vector store created successfully."})
                except Exception as e:
                    yield json.dumps({"event": "error", "data": f"Error creating vector store: {str(e)}"})
                    return  # Exit the generator without returning a value

            yield json.dumps({"event": "status", "data": "Analyzing schema..."})
            sql_query_explanation = generate_sql_query_with_llm(
                user_query=query_text,
                chat_history=chat_history,
                embeddings=embeddings,
                llm=llm,
                vector_store_path=VECTOR_STORE_PATH
            )
            yield json.dumps({"event": "status", "data": "Generating SQL..."})
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
async def execute_query_endpoint(request: Request):
    """Endpoint to execute SQL query."""
    if not hasattr(app.state, 'db_credentials'):
        raise HTTPException(status_code=400, detail="Database credentials not provided. Please connect to database first.")

    request_body = await request.json()
    sql_query = request_body.get("sql_query")

    if not sql_query:
        raise HTTPException(status_code=400, detail="SQL query is required.")

    db_credentials = app.state.db_credentials

    results, columns, error = execute_sql_query(sql_query, db_credentials)
    formatted_results = format_results(results, columns, error)
    return {"results": formatted_results, "error": error}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


