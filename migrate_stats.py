import sqlite3
import os

db_path = 'app.db' # Based on previous context

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Update offers table
    try:
        cursor.execute("ALTER TABLE offers ADD COLUMN is_generated BOOLEAN DEFAULT 0")
        print("Added is_generated to offers")
    except sqlite3.OperationalError:
        print("is_generated already exists")
        
    try:
        cursor.execute("ALTER TABLE offers ADD COLUMN source_offers TEXT")
        print("Added source_offers to offers")
    except sqlite3.OperationalError:
        print("source_offers already exists")
        
    # 2. Update offer_statistics table
    try:
        cursor.execute("ALTER TABLE offer_statistics ADD COLUMN views INTEGER DEFAULT 0")
        print("Added views to offer_statistics")
    except sqlite3.OperationalError:
        print("views already exists")
        
    try:
        cursor.execute("ALTER TABLE offer_statistics ADD COLUMN conversions INTEGER DEFAULT 0")
        print("Added conversions to offer_statistics")
    except sqlite3.OperationalError:
        print("conversions already exists")

    try:
        cursor.execute("ALTER TABLE offer_statistics ADD COLUMN updated_at DATETIME")
        print("Added updated_at to offer_statistics")
    except sqlite3.OperationalError:
        print("updated_at already exists")
        
    conn.commit()
    conn.close()
    print("Migration complete.")
else:
    print(f"Database {db_path} not found.")
