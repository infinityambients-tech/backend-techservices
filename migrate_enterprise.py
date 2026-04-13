import sqlite3
import os

def migrate():
    db_path = 'instance/app.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Tenants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT UNIQUE,
                company_name TEXT,
                company_nip TEXT,
                company_address TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Add tenant_id to existing tables
        tables_to_update = ['users', 'offers', 'reservations', 'payments']
        for table in tables_to_update:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN tenant_id TEXT REFERENCES tenants(id)")
            except sqlite3.OperationalError:
                pass # Already exists

        # Invoices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id TEXT PRIMARY KEY,
                tenant_id TEXT REFERENCES tenants(id),
                user_id TEXT NOT NULL,
                reservation_id TEXT REFERENCES reservations(id),
                payment_id TEXT REFERENCES payments(id),
                invoice_number TEXT UNIQUE,
                net_amount INTEGER,
                vat_rate INTEGER,
                vat_amount INTEGER,
                gross_amount INTEGER,
                currency TEXT DEFAULT 'PLN',
                buyer_name TEXT,
                buyer_address TEXT,
                buyer_nip TEXT,
                pdf_url TEXT,
                issued_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        # Invoice Sequences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                last_value INTEGER DEFAULT 0
            )
        ''')
        
        print("Enterprise Expansion tables (Tenants, Invoices) initialized and existing tables updated.")
    except sqlite3.OperationalError as e:
        print(f"Migration Error: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
