"""
Project and MetadataKey database models.
"""

import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


def generate_uuid() -> str:
    """Generate UUID as string."""
    return str(uuid.uuid4())


class MetadataType(str, enum.Enum):
    """Supported metadata value types."""

    STRING = "string"
    INT = "int"
    BOOL = "bool"
    ENUM = "enum"


class Project(Base):
    """
    Project model - top-level container for organizing work.

    Each project has its own:
    - API keys
    - Metadata configuration
    - Execution logs
    """

    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    metadata_keys = relationship(
        "MetadataKey", back_populates="project", cascade="all, delete-orphan"
    )
    api_keys = relationship(
        "ApiKey", back_populates="project", cascade="all, delete-orphan")
    execution_logs = relationship(
        "ExecutionLog", back_populates="project", cascade="all, delete-orphan"
    )
    policy = relationship(
        "Policy", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="project", cascade="all, delete-orphan"
    )


class MetadataKey(Base):
    """
    Metadata key configuration.

    Defines what metadata fields are valid for a project.
    Supports typed fields: string, int, bool, enum.
    Example: user_id (string), retries (int), is_production (bool), environment (enum).
    """

    __tablename__ = "metadata_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey(
        "projects.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required = Column(Boolean, default=False)

    # Type information
    value_type = Column(Enum(MetadataType), nullable=False,
                        default=MetadataType.STRING)
    # For enum type: list of allowed values
    enum_values = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="metadata_keys")

    # Composite unique constraint on project + key
    __table_args__ = (UniqueConstraint(
        "project_id", "key", name="uq_project_metadata_key"),)
