from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from typing import List, Dict
from app.config import load_env_variables
from app.llm.prompts import get_prompt_template
from app.llm.vector_store import get_relevant_info


def initialize_llm():
    """Initialize Azure OpenAI LLM and Embeddings."""
    env_vars = load_env_variables()
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=env_vars['azure_endpoint'],
        api_key=env_vars['api_key'],
        api_version=env_vars['api_version'],
        azure_deployment=env_vars['embedding_deployment']
    )

    llm = AzureChatOpenAI(
        azure_endpoint=env_vars['azure_endpoint'],
        api_key=env_vars['api_key'],
        api_version=env_vars['api_version'],
        azure_deployment=env_vars['chat_deployment'],
        temperature=0
    )
    return llm, embeddings


def generate_sql_query_with_llm(
    user_query: str,
    chat_history: List[Dict[str, str]],
    embeddings: AzureOpenAIEmbeddings,
    llm: AzureChatOpenAI,
    vector_store_path: str,
    db_type: str
) -> str:
    """Generate SQL query using context and chat history."""

    schema_context, metadata_context = get_relevant_info(
        user_query,
        embeddings,
        vector_store_path 
    )

    if not schema_context:
        return "Error: No schema information available."

    # Convert chat history to string format
    history_str = "\n".join([
        f"User: {msg['content']}" if msg['role'] == 'user' else f"Assistant: {msg['content']}"
        for msg in chat_history[-6:]  # Last 3 exchanges (6 messages)
    ])

    try:
        # Get dynamic prompt template based on user query
        prompt_template = get_prompt_template(user_query, db_type)
        
        print('prompt_template:', prompt_template)
        # If metadata_context is empty, provide a placeholder
        context_to_use = metadata_context if metadata_context else "No additional context available."
        
        chain = prompt_template | llm
        response = chain.invoke({
            "schema": schema_context,
            "context": context_to_use,
            "history": history_str,
            "query": user_query
        })
        return response.content
    except Exception as e:
        return f"Error generating query: {str(e)}"
    