from Tables import tables, tables_columns, tables_data
from LangChain import get_chain
import pandas as pd

import streamlit as st

# Streamlit cloud version is too old, cannot update with pip. With pysqlite3-binary in requirements.txt...
import('pysqlite3') import sys sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# Initialize chain
chain = get_chain(1)
# Callback to get_chain when k is changed
def get_new_k():
    chain = get_chain(st.session_state["top_k_select"])
st.title("Database Query Assistant")

TabMain, TabPreview = st.tabs(["Assistant","Data Preview"])

with TabMain:

    top_k_select = st.selectbox(
        label="How many results should be returned?",
        options=("1", "5", "10", "50", "100", "500", "1000"),
        key="top_k_select",
        on_change=get_new_k
    )

    st.subheader("Question: ")
    question = st.text_input("")

    if question:
        resp = chain.invoke(question)
        
        st.subheader("Answer: ")
        st.write(resp['result'])
        st.subheader("mySQL Query: ")
        st.write(resp['intermediate_steps'][1])

with TabPreview:
    st.caption('''The Database Query Assistant is currently connected to Sakila sample database.
             The database schema models a DVD rental business. Below are samples of each available table.''')
    for t in range(0, len(tables)-1):
        st.subheader(tables[t])
        df = pd.DataFrame(columns=tables_columns[t], data=tables_data[t])
        st.dataframe(df)
