import os
import pyodbc

# Configuration
db_azure_server = os.environ['DB_SERVER']
db_server = f'{db_azure_server}.database.windows.net'
db_database = os.environ['DB_DATABASE']

connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server={db_server};Database={db_database};Authentication=ActiveDirectoryMsi"

with pyodbc.connect(connection_string) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT getdate()")
        row = cursor.fetchone()
        print(row[0])    
