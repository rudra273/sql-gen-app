# from langchain.prompts import ChatPromptTemplate

# PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
#     ("system", """You are an expert SQL query generator that provides helpful explanations. Generate queries based on the provided schema, context, and chat history.


# Rules:
# 1. Use ONLY tables and columns from the schema
# 2. Follow the exact schema for names
# 3. Add additinal context from Additinal context 
# 4. Ensure proper JOIN conditions
# 5. Handle NULL values appropriately
# 6. Ensure string comparisons are case-insensitive using ILIKE
# 7. First provide a brief short explanation of what the query will do
# 8. Then provide the SQL query


# For follow-up questions, use the chat history to maintain context and modify previous queries appropriately."""),
#     ("human", """Schema Information:
# {schema}


# Additional Context:
# {context}


# Recent Chat History:
# {history}


# User Query: {query}


# Generate explanation and SQL query:""")
# ])


# ----------------------------------------------------------------------------------------------------------------

# from langchain.prompts import ChatPromptTemplate
# from app.llm.rules_engine import get_query_specific_rules

# def get_prompt_template(user_query):
#     # Get query-specific rules
#     rules = get_query_specific_rules(user_query)
#     rules_text = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(rules)])
#     # print('rules_text', rules_text)
    
#     return ChatPromptTemplate.from_messages([
#         ("system", f"""You are an expert PostgreSQL query generator that provides helpful explanations. Generate queries based on the provided schema, context, and chat history.

#         Rules:
#         {rules_text}

#         First provide a brief short explanation of what the query will do
#         Then provide the SQL query

#         For follow-up questions, use the chat history to maintain context and modify previous queries appropriately."""),
#                 ("human", """Schema:
#         {schema}

#         Additional Context:
#         {context}

#         Recent Chat History:
#         {history}

#         User Query: {query}

#         Generate explanation and SQL query:""")
#             ])



# rules = get_query_specific_rules('date from table1')
# rules_text = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(rules)])
# print(rules_text)

# ---------------------------------------------------------------------------------------------------------------

from langchain.prompts import ChatPromptTemplate
from app.llm.rules_engine import get_query_specific_rules

def get_prompt_template(user_query, db_type):
    # Get query-specific rules
    rules = get_query_specific_rules(user_query)
    rules_text = "\n".join([f"{i+1}. {rule}" for i, rule in enumerate(rules)])
    
    return ChatPromptTemplate.from_messages([
        ("system", f"""You are an expert {db_type} query generator that provides helpful explanations. Generate queries based on the provided schema, context, and chat history.

        Rules:
        {rules_text}

        dont provide a brief short explanation of what the query will do.
        just provide the SQL query.

        For follow-up questions, use the chat history to maintain context and modify previous queries appropriately."""),
                ("human", """Schema:
        {schema}

        Additional Context:
        {context}

        Recent Chat History:
        {history}

        User Query: {query}

        Generate explanation and SQL query:""")
            ])

