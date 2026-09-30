from sqlalchemy import text
from backend.database.session import engine

def add_missing_columns():
    """Add missing columns to users table"""
    with engine.connect() as conn:
        # Add last_login_at column
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP NULL
        """))
        
        # Add other missing columns
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP NULL
        """))
        
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255) NULL
        """))
        
        conn.commit()
        print("✅ Missing columns added successfully")

if __name__ == "__main__":
    add_missing_columns()