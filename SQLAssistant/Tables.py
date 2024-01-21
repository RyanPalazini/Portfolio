import mysql.connector
import streamlit as st

# Changed to using streamlit's st.secrets[]
# from dotenv import load_dotenv
# import os
# load_dotenv()

cnx = mysql.connector.connect(
    host=st.secrets["db_host"], 
    user=st.secrets["db_user"],  
    password = st.secrets["db_password"],
    port=st.secrets["db_port"],
    db=st.secrets["db_name"]
)

tables = []
tables_columns = []
tables_data = []

cursor = cnx.cursor()
cursor.execute("SHOW tables")

for i in cursor.fetchall(): 
    tables.append(i[0])
    
for table in tables:
    cursor.execute(f"select * from {table} LIMIT 2")
    tables_columns.append(cursor.column_names)
    tables_data.append(cursor.fetchall())

cursor.close()
cnx.close()