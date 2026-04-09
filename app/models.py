import mysql.connector
from mysql.connector import Error
import os

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            port=int(os.environ.get("DB_PORT", 3306)),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME"),
            use_pure=True
        )

        if conn.is_connected():
            return conn

    except Error as e:
        print(f"Error while connecting to Mysql: {e}")
        return None