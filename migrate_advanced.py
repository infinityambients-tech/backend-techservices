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
        # Coupons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id TEXT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                discount_type TEXT NOT NULL,
                value INTEGER NOT NULL,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0,
                valid_until DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Subscription Plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                paypal_plan_id TEXT,
                price INTEGER NOT NULL,
                interval TEXT DEFAULT "month",
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                paypal_subscription_id TEXT,
                status TEXT DEFAULT "pending",
                current_period_end DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        # Connected Accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connected_accounts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                paypal_email TEXT,
                merchant_id TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        print("Advanced features tables (Coupons, Subscriptions, Marketplace) initialized successfully.")
    except sqlite3.OperationalError as e:
        print(f"Migration Error: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
