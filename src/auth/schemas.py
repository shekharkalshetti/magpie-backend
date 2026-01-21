"""
Pydantic schemas for API key endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """Request body for creating an API key."""

    name: str | None = Field(None, max_length=255,
                             description="Human-readable name for the key")


class ApiKeyResponse(BaseModel):
    """Response model for an API key (without plaintext key)."""

    id: str
    project_id: str
    key_prefix: str
    name: str | None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None

    @classmethod
    def from_orm_model(cls, api_key) -> "ApiKeyResponse":
        """Convert ApiKey ORM model to response."""
        return cls(
            id=api_key.id,
            project_id=api_key.project_id,
            key_prefix=api_key.key_prefix,
            name=api_key.name,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
        )


class GeneratedApiKeyResponse(ApiKeyResponse):
    """Response model for a newly created API key (includes plaintext key)."""

    api_key: str = Field(...,
                         description="Plaintext API key - store securely, won't be shown again")

    @classmethod
    def from_orm_model(cls, api_key, plaintext_key: str) -> "GeneratedApiKeyResponse":
        """Convert ApiKey ORM model to response with plaintext key."""
        base = ApiKeyResponse.from_orm_model(api_key)
        return cls(**base.model_dump(), api_key=plaintext_key)
