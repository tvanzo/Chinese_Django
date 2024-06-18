import psycopg2
import os
import socket

DATABASE_URL = os.getenv('DATABASE_URL')

hostname = DATABASE_URL.split('@')[1].split('/')[0].split(':')[0]

try:
    # Check if the hostname resolves
    print(f"Resolving hostname: {hostname}")
    ip = socket.gethostbyname(hostname)
    print(f"Hostname {hostname} resolved to {ip}")

    conn = psycopg2.connect(DATABASE_URL)
    print("Database connection successful")
    conn.close()
except Exception as e:
    print(f"Database connection failed: {e}")
