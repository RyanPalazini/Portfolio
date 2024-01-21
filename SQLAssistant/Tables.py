import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
cnx = mysql.connector.connect(
    host=os.environ["db_host"], 
    user=os.environ["db_user"],  
    password = os.environ["db_password"],
    port=os.environ["db_port"],
    db=os.environ["db_name"]
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