import mysql.connector
from mysql.connector import Error
import os


def get_connection():
    try:

        # This ensures the code finds ca.pem regardless of where you run the script from
        base_path = os.path.dirname(os.path.abspath(__file__))
        cert_path = os.path.join(base_path, "ca.pem")

        conn =  mysql.connector.connect(
            host="mysql-2420b97f-alanjoseph.j.aivencloud.com",
            port=19150,
            user="avnadmin",
            password="AVNS_-omvYPudqpObIUs4hqd",
            database="collegedb",
            
        
            use_pure=True  # <--- CRITICAL: This fixes the Windows SSL error
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error while connecting to Mysql: {e}")
        return None 