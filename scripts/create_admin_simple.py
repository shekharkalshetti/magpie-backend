#!/usr/bin/env python3
"""
Simple script to create an admin user without importing all models
"""
from src.auth.utils import get_password_hash
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

    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    # Hash the password
    hashed_password = get_password_hash(admin_password)

    with engine.connect() as conn:
        # Check if admin user already exists
        result = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email}
        )

        if result.fetchone():
            print(f"✅ Admin user {admin_email} already exists")
            return

        # Create admin user
        conn.execute(
            text("""
                INSERT INTO users (email, hashed_password, is_active, is_superuser, created_at, updated_at)
                VALUES (:email, :password, true, true, NOW(), NOW())
            """),
            {"email": admin_email, "password": hashed_password}
        )
        conn.commit()

        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   Please change this password after first login!")


if __name__ == "__main__":
    try:
        create_admin_user()
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
