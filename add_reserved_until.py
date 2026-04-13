import sqlite3

def migrate():
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE time_slots ADD COLUMN reserved_until DATETIME')
        print("Column 'reserved_until' added to 'time_slots' table.")
    except sqlite3.OperationalError as e:
        print(f"Migration Error: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
