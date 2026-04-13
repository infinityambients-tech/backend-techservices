import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if not os.path.exists(db_path):
    print(f"Error: {db_path} does not exist")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(reservations)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'payment_status' in columns:
        print("SUCCESS: 'payment_status' column found in 'reservations' table.")
    else:
        print(f"FAILURE: 'payment_status' column NOT found. Columns: {columns}")
except Exception as e:
    print(f"Error checking schema: {e}")
finally:
    conn.close()
