from langchain_google_genai import GoogleGenerativeAI 
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import SemanticSimilarityExampleSelector, FewShotPromptTemplate
# from langchain.chains.sql_database.prompt import PROMPT_SUFFIX, _mysql_prompt
from prompts import prompt_suffix, mysql_prompt, few_shots
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts.prompt import PromptTemplate
import streamlit as st

# Changed to using streamlit's st.secrets[]
# from dotenv import load_dotenv
# import os
# load_dotenv()

def get_chain(top_k): 
    llm = GoogleGenerativeAI(model="models/gemini-pro", google_api_key=st.secrets['google_api_key'], temperature=0)
   
    db_user = st.secrets["db_user"]
    db_password = st.secrets["db_password"]
    db_host = st.secrets["db_host"]
    db_name = st.secrets["db_name"]
    db = SQLDatabase.from_uri(
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",
        sample_rows_in_table_info=3
    )

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    to_vectorize = [" ".join(example.values()) for example in few_shots]
    vectorstore = Chroma.from_texts(to_vectorize, embedding=embeddings, metadatas=few_shots)

    # Include buffer memory to allow user to revise recently requested queries
    # memory = ConversationBufferWindowMemory(k=5)

    # Adding {History} to Langchain's built-in PROMPT_SUFFIX. This will enable LLM to utilize ConversationBufferMemory.
    # prompt_suffix = 'Only use the following tables:\n{table_info}\n\nRelevant pieces of previous conversation (You do not need to use these pieces of information if not relevant):\n{history}\n\nQuestion: {input}'

    example_prompt = PromptTemplate(
        input_variables=["Question", "SQLQuery", "SQLResult", "Answer"],
        template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}"
    )

    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=1
    )

    few_shot_prompt = FewShotPromptTemplate(
        # example_selector will establish connection to vector DB
        example_selector=example_selector,
        example_prompt=example_prompt,
        # Langchain's _mysql_prompt helps LLM to avoid common mistakes
        prefix=mysql_prompt,
        suffix=prompt_suffix,
        # Add "history" if using memory and a revised prompt_suffix
        input_variables=["input", "table_info", "top_k"]
    )

    chain = SQLDatabaseChain.from_llm(
        llm, 
        db,
        # memory=memory,
        verbose=True,
        use_query_checker=True,
        prompt=few_shot_prompt,
        return_intermediate_steps=True,
        top_k=top_k
    )
    return chain

# if __name__ == "__main__":
#   chain = get_chain(5)
#   print(chain.invoke()