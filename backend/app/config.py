import os
from dotenv import load_dotenv

def load_env_variables():
    """Load environment variables"""
    load_dotenv()
    return {
        'azure_endpoint': os.getenv("AZURE_OPENAI_ENDPOINT"),
        'api_key': os.getenv("AZURE_OPENAI_API_KEY"),
        'api_version': "2024-02-01",
        'chat_deployment': os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        'embedding_deployment': 'text-embedding-ada-002',
        # 'db_name': os.getenv("POSTGRES_DB"),
        # 'db_user': os.getenv("POSTGRES_USER"),
        # 'db_password': os.getenv("POSTGRES_PASSWORD"),
        # 'db_host': os.getenv("POSTGRES_HOST"),
        # 'db_port': os.getenv("POSTGRES_PORT")
    }