"""
API Key database model.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


def generate_uuid() -> str:
    """Generate UUID as string."""
    return str(uuid.uuid4())


class ApiKey(Base):
    """
    API key for authentication.

    Scoped to a specific project. Used by SDK to authenticate requests.
    Keys are stored hashed for security.
    """

    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = Column(String(10), nullable=False)  # First few chars for identification
    name = Column(String(255), nullable=True)  # Human-readable name
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="api_keys")
