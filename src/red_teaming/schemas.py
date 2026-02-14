"""Pydantic schemas for red teaming API."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Template Schemas
# ============================================================================

class TemplateVariableSchema(BaseModel):
    """Schema for template variable definition."""
    type: str = Field(...,
                      description="Variable type: string, random_choice, base64_encode")
    default: Optional[str] = Field(
        None, description="Default value if not provided")
    choices: Optional[List[str]] = Field(
        None, description="Available choices for random_choice type")
    description: Optional[str] = Field(
        None, description="Human-readable description")


class RedTeamTemplateResponse(BaseModel):
    """Response schema for attack template."""
    id: str
    name: str
    category: str
    severity: str
    description: Optional[str] = None
    template_text: str
    variables: Optional[Dict[str, Any]] = None
    expected_behavior: Optional[Dict[str, Any]] = None
    is_active: bool
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateTemplateRequest(BaseModel):
    """Request schema for creating custom template."""
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., description="Attack category")
    severity: str = Field(..., description="Attack severity level")
    description: Optional[str] = None
    template_text: str = Field(..., min_length=1)
    variables: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None


class UpdateTemplateRequest(BaseModel):
    """Request schema for updating template."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    template_text: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# ============================================================================
# Campaign Schemas
# ============================================================================

class CreateCampaignRequest(BaseModel):
    """Request schema for creating red team campaign."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    attack_categories: List[str] = Field(...,
                                         min_items=1, description="Categories to test")
    target_model: Optional[str] = None
    attacks_per_template: int = Field(default=1, ge=1, le=50)
    fail_threshold_percent: Optional[float] = Field(None, ge=0, le=100)


class UpdateCampaignRequest(BaseModel):
    """Request schema for updating campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None


class RedTeamCampaignResponse(BaseModel):
    """Response schema for campaign."""
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    attack_categories: List[str]
    target_model: Optional[str] = None
    attacks_per_template: int
    fail_threshold_percent: Optional[float] = None
    status: str
    total_attacks: int
    successful_attacks: int
    failed_attacks: int
    success_rate: Optional[float] = None
    risk_level: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Response schema for campaign list."""
    items: List[RedTeamCampaignResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# Attack Schemas
# ============================================================================

class RedTeamAttackResponse(BaseModel):
    """Response schema for individual attack."""
    id: str
    campaign_id: str
    template_id: Optional[str] = None
    execution_log_id: Optional[str] = None
    project_id: str
    attack_type: str
    attack_name: str
    attack_prompt: str
    template_variables: Optional[Dict[str, Any]] = None
    llm_response: Optional[str] = None
    llm_model: Optional[str] = None
    was_successful: Optional[bool] = None
    bypass_score: Optional[float] = None
    analysis_notes: Optional[str] = None
    flagged_policies: Optional[List[str]] = None
    review_queue_id: Optional[str] = None
    severity: str
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttackListResponse(BaseModel):
    """Response schema for attack list."""
    items: List[RedTeamAttackResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# Quick Test Schemas
# ============================================================================

class QuickTestRequest(BaseModel):
    """Request schema for quick single attack test."""
    template_id: str = Field(..., description="Template ID to use")
    variables: Optional[Dict[str, str]] = Field(
        None, description="Variable overrides")
    target_model: Optional[str] = None


class QuickTestResponse(BaseModel):
    """Response schema for quick test result."""
    attack_id: str
    attack_name: str
    attack_type: str
    attack_prompt: str
    llm_response: Optional[str] = None
    was_successful: Optional[bool] = None
    bypass_score: Optional[float] = None
    analysis_notes: Optional[str] = None
    severity: str
    execution_time_ms: Optional[int] = None
    review_queue_id: Optional[str] = None


# ============================================================================
# Statistics Schemas
# ============================================================================

class CampaignStatsResponse(BaseModel):
    """Response schema for campaign statistics."""
    total_campaigns: int
    active_campaigns: int
    total_attacks_run: int
    total_successful_attacks: int
    overall_success_rate: float
    risk_level: str
    vulnerabilities_by_category: Dict[str, int]
    recent_campaigns: List[RedTeamCampaignResponse]


class VulnerabilitySummary(BaseModel):
    """Summary of a vulnerability."""
    attack_id: str
    attack_name: str
    attack_type: str
    severity: str
    bypass_score: Optional[float] = None
    created_at: datetime


class ProjectSecurityReport(BaseModel):
    """Security report for a project."""
    project_id: str
    total_tests: int
    vulnerabilities_found: int
    risk_level: str
    last_test_date: Optional[datetime] = None
    trend: str  # "improving", "degrading", "stable"
    critical_vulnerabilities: List[VulnerabilitySummary]
    recommendations: List[str]
