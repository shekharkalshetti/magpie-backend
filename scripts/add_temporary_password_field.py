"""
Migration script to add temporary_password field to user_invitations table.

Usage:
    cd backend
    python scripts/add_temporary_password_field.py
"""

from src.database import SessionLocal, engine
import sys
import os
from sqlalchemy import text

# Set up path
os.chdir(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, ".")


def migrate():
    """Add temporary_password field to user_invitations table."""
    with engine.connect() as connection:
        # Check if column already exists
        try:
            inspector_query = """
                SELECT COUNT(*) FROM information_schema.COLUMNS 
                WHERE TABLE_NAME = 'user_invitations' 
                AND COLUMN_NAME = 'temporary_password'
            """
            result = connection.execute(text(inspector_query))
            count = result.scalar()

            if count > 0:
                print("✓ Column 'temporary_password' already exists in user_invitations")
                return
        except Exception:
            # SQLite doesn't have information_schema, try the column directly
            pass

        # Add the column
        try:
            connection.execute(
                text("""
                    ALTER TABLE user_invitations 
                    ADD COLUMN temporary_password VARCHAR(255) NULL
                """)
            )
            connection.commit()
            print(
                "✓ Successfully added 'temporary_password' field to user_invitations table")
        except Exception as e:
            print(f"✗ Error adding column: {e}")
            if "already exists" in str(e).lower():
                print("  (Column already exists, this is OK)")
            else:
                raise


if __name__ == "__main__":
    migrate()
