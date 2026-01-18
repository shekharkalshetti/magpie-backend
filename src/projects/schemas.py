"""
Pydantic schemas for project and metadata key endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Import MetadataType from models - but use TYPE_CHECKING to avoid circular imports
# at runtime we import from the local models file since schemas don't trigger mapper config
from src.projects.models import MetadataType
from src.schemas import CustomBaseModel

# ============================================================================
# Project Schemas
# ============================================================================


class ProjectCreate(BaseModel):
    """Request body for creating a project."""

    name: str = Field(..., min_length=1, max_length=255,
                      description="Project name")
    description: str | None = Field(None, description="Project description")


class ProjectResponse(CustomBaseModel):
    """Response model for a project."""

    project_id: str = Field(..., description="Unique project identifier")
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_orm_model(cls, project) -> "ProjectResponse":
        """Convert Project ORM model to response."""
        return cls(
            project_id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


# ============================================================================
# Metadata Key Schemas
# ============================================================================


class MetadataKeyCreate(BaseModel):
    """Request body for creating a metadata key."""

    key: str = Field(..., min_length=1, max_length=255,
                     description="Metadata key name")
    description: str | None = Field(
        None, description="Optional description of the metadata key")
    required: bool = Field(
        False, description="Whether this metadata key is required")
    value_type: MetadataType = Field(
        MetadataType.STRING, description="Data type for this metadata key"
    )
    enum_values: list[str] | None = Field(
        None, description="Allowed values (only for enum type)")

    @field_validator("enum_values")
    @classmethod
    def validate_enum_values(cls, v, info):
        """Ensure enum_values is only provided for enum type."""
        if info.data.get("value_type") == MetadataType.ENUM:
            if not v or len(v) == 0:
                raise ValueError(
                    "enum_values is required when value_type is 'enum'")
        elif v is not None:
            raise ValueError(
                "enum_values should only be provided when value_type is 'enum'")
        return v


class MetadataKeyResponse(CustomBaseModel):
    """Response model for a metadata key."""

    id: str
    project_id: str
    key: str
    description: str | None = None
    required: bool
    value_type: MetadataType
    enum_values: list[str] | None = None
    created_at: datetime
