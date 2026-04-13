import sqlite3
import os

db_path = os.path.join('instance', 'app.db')
if not os.path.exists(db_path):
    print(f"Database {db_path} not found. Creating it...")
    # Trigger creation by running app.py briefly or just using sqlite
    # But let's just create it here if possible.
    # Actually, it's better to let Flask create it.

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE reservations ADD COLUMN payment_status VARCHAR(20) DEFAULT 'unpaid'")
    print("Column 'payment_status' added successfully to 'reservations'.")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e).lower():
        print("Column 'payment_status' already exists.")
    else:
        print(f"Error adding column: {e}")
finally:
    conn.commit()
    conn.close()
