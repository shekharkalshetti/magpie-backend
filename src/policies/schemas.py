"""
Pydantic schemas for policy endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.policies.constants import PolicySeverity
from src.schemas import CustomBaseModel


# ============================================================================
# Detection Option Schemas
# ============================================================================


class DetectionOptionBase(BaseModel):
    """Base schema for detection options."""

    id: str = Field(..., description="Unique option identifier")
    label: str = Field(..., description="Human-readable label")
    enabled: bool = Field(True, description="Whether this option is enabled")


class DetectionOptionUpdate(BaseModel):
    """Schema for updating a detection option."""

    enabled: bool = Field(..., description="Whether this option is enabled")


# ============================================================================
# Policy Section Schemas
# ============================================================================


class PolicySectionBase(BaseModel):
    """Base schema for policy sections."""

    id: str = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section title")
    severity: PolicySeverity = Field(..., description="Severity level")
    description: str = Field(..., description="Section description")
    policy_text: str = Field(..., description="Policy text/rules")
    enabled: bool = Field(True, description="Whether this section is enabled")
    options: list[DetectionOptionBase] = Field(
        default_factory=list, description="Detection options"
    )


class PolicySectionUpdate(BaseModel):
    """Schema for updating a policy section."""

    enabled: bool | None = Field(
        None, description="Whether this section is enabled")
    policy_text: str | None = Field(None, description="Updated policy text")


# ============================================================================
# Policy Category Schemas
# ============================================================================


class PolicyCategoryBase(BaseModel):
    """Base schema for policy categories."""

    id: str = Field(..., description="Unique category identifier")
    name: str = Field(..., description="Category name")
    enabled: bool = Field(True, description="Whether this category is enabled")
    sections: list[PolicySectionBase] = Field(
        default_factory=list, description="Sections in this category"
    )


class PolicyCategoryUpdate(BaseModel):
    """Schema for updating a policy category."""

    enabled: bool = Field(..., description="Whether this category is enabled")


# ============================================================================
# Policy Schemas
# ============================================================================


class PolicyConfigSchema(BaseModel):
    """Schema for the full policy configuration."""

    categories: list[PolicyCategoryBase] = Field(
        default_factory=list, description="Policy categories"
    )


class PolicyCreate(BaseModel):
    """Request body for creating a policy."""

    config: PolicyConfigSchema | None = Field(
        None, description="Optional custom configuration (uses defaults if not provided)"
    )


class PolicyUpdate(BaseModel):
    """Request body for updating a policy."""

    is_active: bool | None = Field(
        None, description="Whether the policy is active")
    config: PolicyConfigSchema | None = Field(
        None, description="Full policy configuration")


class PolicyResponse(CustomBaseModel):
    """Response model for a policy."""

    id: str = Field(..., description="Unique policy identifier")
    project_id: str = Field(..., description="Associated project ID")
    is_active: bool = Field(..., description="Whether the policy is active")
    config: dict[str, Any] = Field(..., description="Policy configuration")
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_orm_model(cls, policy) -> "PolicyResponse":
        """Convert Policy ORM model to response."""
        return cls(
            id=policy.id,
            project_id=policy.project_id,
            is_active=policy.is_active,
            config=policy.config,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )


class PolicySummaryResponse(CustomBaseModel):
    """Summary response for a policy (without full config)."""

    id: str
    project_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_orm_model(cls, policy) -> "PolicySummaryResponse":
        """Convert Policy ORM model to summary response."""
        return cls(
            id=policy.id,
            project_id=policy.project_id,
            is_active=policy.is_active,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )


class SystemPromptResponse(CustomBaseModel):
    """Response containing the generated system prompt."""

    policy_id: str
    project_id: str
    system_prompt: str = Field(...,
                               description="Generated system prompt for LLM")
    enabled_options_count: int = Field(
        ..., description="Total number of enabled detection options"
    )


# ============================================================================
# Bulk Update Schemas
# ============================================================================


class OptionToggleRequest(BaseModel):
    """Request to toggle a specific option."""

    category_id: str = Field(..., description="Category ID")
    section_id: str = Field(..., description="Section ID")
    option_id: str = Field(..., description="Option ID")
    enabled: bool = Field(..., description="New enabled state")


class SectionToggleRequest(BaseModel):
    """Request to toggle a specific section."""

    category_id: str = Field(..., description="Category ID")
    section_id: str = Field(..., description="Section ID")
    enabled: bool = Field(..., description="New enabled state")


class CategoryToggleRequest(BaseModel):
    """Request to toggle a specific category."""

    category_id: str = Field(..., description="Category ID")
    enabled: bool = Field(..., description="New enabled state")


class BulkToggleRequest(BaseModel):
    """Request for bulk toggle operations."""

    categories: list[CategoryToggleRequest] | None = None
    sections: list[SectionToggleRequest] | None = None
    options: list[OptionToggleRequest] | None = None
