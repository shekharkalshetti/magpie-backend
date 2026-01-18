"""
Database configuration and session management.

Provides SQLAlchemy engine, session factory, and naming conventions.
"""

from collections.abc import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.config import settings

# PostgreSQL naming conventions for indexes and constraints
# This ensures consistent, predictable naming across the database
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

# Create metadata with naming conventions
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models - uses our custom metadata with naming conventions
Base = declarative_base(metadata=metadata)


def create_tables():
    """Create all database tables defined in models."""
    Base.metadata.create_all(bind=engine)


async def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get a database session.

    Usage:
        @router.get("/items")
        async def read_items(db: Session = Depends(get_db)):
            ...

    Note: Using async def for consistency with async routes,
    even though the actual DB operations are sync.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
