# update_prediction_field_length.py
"""
Database migration to update prediction field length from String(10) to String(20)
This allows storing 'UNABLE_TO_ANALYZE' and other longer prediction values.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.postgres_connection import get_db, test_connection
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Update prediction field length in prediction_results table"""
    
    if not test_connection():
        logger.error("❌ Cannot connect to database")
        return False
    
    try:
        db = next(get_db())
        
        # Check current column length
        logger.info("🔍 Checking current prediction field length...")
        result = db.execute(text("""
            SELECT character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'prediction_results' 
            AND column_name = 'prediction'
        """))
        
        current_length = result.fetchone()
        if current_length:
            logger.info(f"📏 Current prediction field length: {current_length[0]}")
        
        # Update the column length
        logger.info("🔄 Updating prediction field length to 20 characters...")
        
        # Use ALTER TABLE to modify the column
        db.execute(text("""
            ALTER TABLE prediction_results 
            ALTER COLUMN prediction TYPE VARCHAR(20)
        """))
        
        db.commit()
        logger.info("✅ Successfully updated prediction field length")
        
        # Verify the change
        result = db.execute(text("""
            SELECT character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'prediction_results' 
            AND column_name = 'prediction'
        """))
        
        new_length = result.fetchone()
        if new_length:
            logger.info(f"📏 New prediction field length: {new_length[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

def rollback_migration():
    """Rollback prediction field length to original size"""
    
    if not test_connection():
        logger.error("❌ Cannot connect to database")
        return False
    
    try:
        db = next(get_db())
        
        logger.info("🔄 Rolling back prediction field length to 10 characters...")
        
        db.execute(text("""
            ALTER TABLE prediction_results 
            ALTER COLUMN prediction TYPE VARCHAR(10)
        """))
        
        db.commit()
        logger.info("✅ Successfully rolled back prediction field length")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("=== Database Migration: Update Prediction Field Length ===")
    print()
    
    print("This migration will update the prediction field in the prediction_results table")
    print("from VARCHAR(10) to VARCHAR(20) to accommodate longer prediction values.")
    print()
    print("New prediction values that will be supported:")
    print("- 'FAKE' (4 chars)")
    print("- 'REAL' (4 chars)")
    print("- 'UNCERTAIN' (8 chars)")
    print("- 'UNABLE_TO_ANALYZE' (16 chars)")
    print()
    
    choice = input("Do you want to run this migration? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("\n🚀 Running migration...")
        success = run_migration()
        
        if success:
            print("✅ Migration completed successfully!")
            print("\nThe enhanced prediction system will now work properly with database storage.")
        else:
            print("❌ Migration failed. Please check the logs above.")
    elif choice == 'rollback':
        print("\n🔄 Rolling back migration...")
        success = rollback_migration()
        
        if success:
            print("✅ Rollback completed successfully!")
        else:
            print("❌ Rollback failed. Please check the logs above.")
    else:
        print("❌ Migration cancelled.")
