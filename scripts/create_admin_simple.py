#!/usr/bin/env python3
"""
Robust script to create an admin user - handles all edge cases
"""
from src.auth.utils import hash_password
from src.config import settings
from sqlalchemy import create_engine, text
import os
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def create_admin_user():
    """Create admin user directly with SQL"""
    engine = create_engine(settings.DATABASE_URL)

    # Get admin credentials from env or use defaults
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@magpie.local')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    print(f"Creating admin user: {admin_email}")

    # Hash the password
    hashed_password = hash_password(admin_password)

    # First, ensure the users table exists (in separate transaction)
    with engine.connect() as conn:
        try:
            conn.execute(text("SELECT 1 FROM users LIMIT 1"))
        except Exception:
            print("Creating users table...")
            conn.rollback()  # Rollback failed transaction
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    is_superuser BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
            print("✅ Users table created")

    # Now create/update admin user (in new transaction)
    with engine.connect() as conn:
        # Check if admin user already exists
        result = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email}
        )

        existing = result.fetchone()
        if existing:
            print(f"✅ Admin user {admin_email} already exists")
            # Update password anyway
            conn.execute(
                text(
                    "UPDATE users SET password_hash = :password, updated_at = NOW() WHERE email = :email"),
                {"email": admin_email, "password": hashed_password}
            )
            conn.commit()
            print(f"✅ Password updated for {admin_email}")
        else:
            # Create admin user
            conn.execute(
                text("""
                    INSERT INTO users (email, password_hash, is_active, is_superuser, created_at, updated_at)
                    VALUES (:email, :password, true, true, NOW(), NOW())
                """),
                {"email": admin_email, "password": hashed_password}
            )
            conn.commit()
            print(f"✅ Admin user created successfully!")

        print(f"\n{'='*50}")
        print(f"Admin Credentials:")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print(f"{'='*50}")
        print(f"\n⚠️  Please change this password after first login!")


if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
