import mysql.connector
import os

def get_connection():
    # This ensures the code finds ca.pem regardless of where you run the script from
    base_path = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(base_path, "ca.pem")

    return mysql.connector.connect(
        host="mysql-2420b97f-alanjoseph.j.aivencloud.com",
        port=19150,
        user="avnadmin",
        password="AVNS_-omvYPudqpObIUs4hqd",
        database="collegedb",
        
        use_pure=True  # <--- CRITICAL: This fixes the Windows SSL error
    )