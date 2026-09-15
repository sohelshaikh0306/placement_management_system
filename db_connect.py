import mysql.connector

conn=mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="placement_db"
)

if conn.is_connected():
    print("Connected to MySQL!")