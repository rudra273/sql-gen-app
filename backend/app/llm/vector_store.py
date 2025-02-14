from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from typing import Tuple, Optional, Dict
import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import load_env_variables 

path = os.path.dirname(os.path.abspath(__file__))

VECTOR_STORE_PATH = f"{path}/vector_store" 

def load_json_file(file_path: str) -> Dict: 
        """Load any JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: File not found: {file_path}")
            return {}
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in file: {file_path}")
            return {}

def create_vector_store_from_files(schema_path: str, metadata_path: Optional[str] = None, persist_dir: str = VECTOR_STORE_PATH) -> None:
    """Create and persist a single vector store containing both schema and metadata."""
    
    # Initialize Azure OpenAI embeddings
    env_vars = load_env_variables()
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=env_vars['azure_endpoint'],
        api_key=env_vars['api_key'],
        api_version=env_vars['api_version'],
        deployment=env_vars['embedding_deployment'],
        chunk_size=1
    )

    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    # Load schema and metadata
    schema = load_json_file(schema_path)
    metadata = load_json_file(metadata_path) if metadata_path else {}
    
    # Combined lists for texts and metadatas
    all_texts = []
    all_metadatas = []
    
    # Process schema
    schema_text = json.dumps(schema, indent=2)
    schema_chunks = text_splitter.split_text(schema_text)
    
    for chunk in schema_chunks:
        all_texts.append(chunk)
        all_metadatas.append({
            "doc_type": "schema"
        })
    
    # Process metadata if available
    if metadata:
        metadata_text = json.dumps(metadata, indent=2)
        metadata_chunks = text_splitter.split_text(metadata_text)
        
        for chunk in metadata_chunks:
            all_texts.append(chunk)
            all_metadatas.append({
                "doc_type": "metadata"
            })
    
    # Create combined vector store if we have any texts
    if all_texts:
        # Create Chroma instance - it will automatically persist
        Chroma.from_texts(
            texts=all_texts,
            metadatas=all_metadatas,
            embedding=embeddings,
            persist_directory=persist_dir
        )
        print(f"Combined vector store created in {persist_dir}")
    else:
        print("No valid data to create vector store")


def get_relevant_info(
    query: str,
    embeddings: AzureOpenAIEmbeddings,
    vector_store_path: str = VECTOR_STORE_PATH,
    num_results: int = 5
) -> Tuple[str, str]:
    """Retrieve relevant schema and metadata"""

    print(f"Vector store path: {vector_store_path}")
    print(f"Query: {query}")
    try:



        vector_store = Chroma(
            persist_directory=vector_store_path,
            embedding_function=embeddings
        )

        schema_results = vector_store.similarity_search(
            query,
            k=num_results,
            filter={"doc_type": "schema"}
        )
        schema_context = "\n\n".join(doc.page_content for doc in schema_results)

        metadata_results = vector_store.similarity_search(
            query,
            k=num_results,
            filter={"doc_type": "metadata"}
        )
        metadata_context = "\n\n".join(doc.page_content for doc in metadata_results) 

        print(f"Schema context: {schema_context}")
        print(f"Metadata context: {metadata_context}") 

        return schema_context, metadata_context
    except Exception as e:
        print(f"Error retrieving context: {str(e)}")
        return "", ""

