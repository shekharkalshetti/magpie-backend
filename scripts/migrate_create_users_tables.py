"""
Database migration script for user authentication.

This creates the necessary tables for user management:
- users
- project_users
- user_invitations
"""

from src.database import Base, engine
from src import models  # noqa: F401


def create_tables():
    """Create all tables in the database."""
    print("Creating database tables...")

    # Create all tables defined in Base
    Base.metadata.create_all(bind=engine)

    print("✓ Database tables created successfully!")


if __name__ == "__main__":
    create_tables()
