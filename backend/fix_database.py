import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def fix_database_schema():
    """Add all missing columns to users table"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "fake_news_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "bilal@3132"),
        port=os.getenv("DB_PORT", "5432")
    )
    
    cursor = conn.cursor()
    
    # List of columns to add
    columns_to_add = [
        "verified_at TIMESTAMP NULL",
        "last_login_at TIMESTAMP NULL", 
        "password_changed_at TIMESTAMP NULL",
        "verification_token VARCHAR(255) NULL",
        "reset_token VARCHAR(255) NULL",
        "reset_token_expires TIMESTAMP NULL", 
        "refresh_token TEXT NULL",
        "failed_login_attempts INTEGER DEFAULT 0",
        "locked_until TIMESTAMP NULL"
    ]
    
    for column_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_def}")
            print(f"✅ Added column: {column_def.split()[0]}")
        except Exception as e:
            print(f"❌ Failed to add column: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 Database schema fixed successfully!")

if __name__ == "__main__":
    fix_database_schema()