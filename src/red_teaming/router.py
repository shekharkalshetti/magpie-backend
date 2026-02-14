"""Red team API router."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.users.router import get_current_user_from_token
from src.users.schemas import UserResponse
from src.models import ProjectUser
from src.red_teaming.service import RedTeamService
from src.red_teaming.schemas import (
    CreateCampaignRequest,
    UpdateCampaignRequest,
    RedTeamCampaignResponse,
    CampaignListResponse,
    RedTeamAttackResponse,
    AttackListResponse,
    RedTeamTemplateResponse,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    QuickTestRequest,
    QuickTestResponse,
    CampaignStatsResponse,
)

router = APIRouter(tags=["Red Teaming"])


def verify_project_access(db: Session, user_id: str, project_id: str):
    """Verify user has access to project."""
    project_user = (
        db.query(ProjectUser)
        .filter_by(user_id=user_id, project_id=project_id)
        .first()
    )
    if not project_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this project",
        )


# ============================================================================
# Campaign Endpoints
# ============================================================================

@router.post(
    "/projects/{project_id}/red-teaming/campaigns",
    response_model=RedTeamCampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create red team campaign",
    description="Create a new red team campaign for security testing",
)
async def create_campaign(
    project_id: str,
    request: CreateCampaignRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Create a new red team campaign."""
    verify_project_access(db, current_user.id, project_id)

    service = RedTeamService(db)
    campaign = service.create_campaign(
        project_id=project_id,
        user_id=current_user.id,
        name=request.name,
        attack_categories=request.attack_categories,
        description=request.description,
        target_model=request.target_model,
        attacks_per_template=request.attacks_per_template,
        fail_threshold_percent=request.fail_threshold_percent,
    )

    return RedTeamCampaignResponse.model_validate(campaign)


@router.get(
    "/projects/{project_id}/red-teaming/campaigns",
    response_model=CampaignListResponse,
    summary="List campaigns",
    description="Get red team campaigns for a project",
)
async def list_campaigns(
    project_id: str,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """List red team campaigns for a project."""
    verify_project_access(db, current_user.id, project_id)

    service = RedTeamService(db)
    campaigns, total = service.get_project_campaigns(
        project_id=project_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )

    return CampaignListResponse(
        items=[RedTeamCampaignResponse.model_validate(c) for c in campaigns],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/red-teaming/campaigns/{campaign_id}",
    response_model=RedTeamCampaignResponse,
    summary="Get campaign",
    description="Get details of a specific campaign",
)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Get campaign details."""
    service = RedTeamService(db)
    campaign = service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    verify_project_access(db, current_user.id, campaign.project_id)

    return RedTeamCampaignResponse.model_validate(campaign)


@router.patch(
    "/red-teaming/campaigns/{campaign_id}",
    response_model=RedTeamCampaignResponse,
    summary="Update campaign",
    description="Update campaign details",
)
async def update_campaign(
    campaign_id: str,
    request: UpdateCampaignRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Update campaign."""
    service = RedTeamService(db)
    campaign = service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    verify_project_access(db, current_user.id, campaign.project_id)

    # Update fields
    if request.name:
        campaign.name = request.name
    if request.description is not None:
        campaign.description = request.description
    if request.status:
        service.update_campaign_status(campaign_id, request.status)

    db.commit()
    db.refresh(campaign)

    return RedTeamCampaignResponse.model_validate(campaign)


@router.post(
    "/red-teaming/campaigns/{campaign_id}/start",
    response_model=RedTeamCampaignResponse,
    summary="Start campaign",
    description="Start executing a campaign (queues background task)",
)
async def start_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Start campaign execution."""
    service = RedTeamService(db)
    campaign = service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    verify_project_access(db, current_user.id, campaign.project_id)

    if campaign.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campaign is already {campaign.status}",
        )

    # Queue campaign execution task
    from src.tasks.red_team_tasks import execute_campaign
    execute_campaign.delay(campaign_id)

    # Update status to running
    service.update_campaign_status(campaign_id, "running")

    db.refresh(campaign)
    return RedTeamCampaignResponse.model_validate(campaign)


@router.post(
    "/red-teaming/campaigns/{campaign_id}/cancel",
    response_model=RedTeamCampaignResponse,
    summary="Cancel campaign",
    description="Cancel a running campaign",
)
async def cancel_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Cancel campaign execution."""
    service = RedTeamService(db)
    campaign = service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    verify_project_access(db, current_user.id, campaign.project_id)

    if campaign.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel campaign with status {campaign.status}",
        )

    service.update_campaign_status(campaign_id, "cancelled")

    db.refresh(campaign)
    return RedTeamCampaignResponse.model_validate(campaign)


# ============================================================================
# Attack Endpoints
# ============================================================================

@router.get(
    "/red-teaming/campaigns/{campaign_id}/attacks",
    response_model=AttackListResponse,
    summary="List campaign attacks",
    description="Get attacks for a campaign",
)
async def list_campaign_attacks(
    campaign_id: str,
    skip: int = 0,
    limit: int = 100,
    successful_only: bool = False,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """List attacks for a campaign."""
    service = RedTeamService(db)
    campaign = service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    verify_project_access(db, current_user.id, campaign.project_id)

    attacks, total = service.get_campaign_attacks(
        campaign_id=campaign_id,
        skip=skip,
        limit=limit,
        successful_only=successful_only,
    )

    return AttackListResponse(
        items=[RedTeamAttackResponse.model_validate(a) for a in attacks],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/red-teaming/attacks/{attack_id}",
    response_model=RedTeamAttackResponse,
    summary="Get attack details",
    description="Get details of a specific attack",
)
async def get_attack(
    attack_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Get attack details."""
    service = RedTeamService(db)
    attack = service.get_attack(attack_id)

    if not attack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attack not found",
        )

    verify_project_access(db, current_user.id, attack.project_id)

    return RedTeamAttackResponse.model_validate(attack)


# ============================================================================
# Template Endpoints
# ============================================================================

@router.get(
    "/red-teaming/templates",
    response_model=List[RedTeamTemplateResponse],
    summary="List attack templates",
    description="Get available attack templates",
)
async def list_templates(
    category: Optional[str] = None,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """List available attack templates."""
    if project_id:
        verify_project_access(db, current_user.id, project_id)

    service = RedTeamService(db)
    templates = service.get_templates(
        category=category,
        project_id=project_id,
        active_only=True,
    )

    return [RedTeamTemplateResponse.model_validate(t) for t in templates]


@router.get(
    "/red-teaming/templates/{template_id}",
    response_model=RedTeamTemplateResponse,
    summary="Get template",
    description="Get details of a specific template",
)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Get template details."""
    service = RedTeamService(db)
    template = service.get_template(template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # If custom template, verify access
    if template.is_custom and template.project_id:
        verify_project_access(db, current_user.id, template.project_id)

    return RedTeamTemplateResponse.model_validate(template)


@router.post(
    "/projects/{project_id}/red-teaming/templates",
    response_model=RedTeamTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom template",
    description="Create a custom attack template",
)
async def create_template(
    project_id: str,
    request: CreateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Create custom attack template."""
    verify_project_access(db, current_user.id, project_id)

    service = RedTeamService(db)
    template = service.create_custom_template(
        name=request.name,
        category=request.category,
        severity=request.severity,
        template_text=request.template_text,
        user_id=current_user.id,
        project_id=request.project_id or project_id,
        description=request.description,
        variables=request.variables,
    )

    return RedTeamTemplateResponse.model_validate(template)


# ============================================================================
# Quick Test Endpoint
# ============================================================================

@router.post(
    "/projects/{project_id}/red-teaming/quick-test",
    response_model=QuickTestResponse,
    summary="Quick attack test",
    description="Run a single attack test immediately",
)
async def quick_test(
    project_id: str,
    request: QuickTestRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Run a quick single attack test."""
    verify_project_access(db, current_user.id, project_id)

    # Queue quick test task
    from src.tasks.red_team_tasks import execute_quick_test
    task = execute_quick_test.delay(
        project_id=project_id,
        template_id=request.template_id,
        variable_values=request.variables,
        target_model=request.target_model,
    )

    # Wait for result (with timeout)
    try:
        result = task.get(timeout=30)
        return QuickTestResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick test failed: {str(e)}",
        )


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get(
    "/projects/{project_id}/red-teaming/stats",
    response_model=CampaignStatsResponse,
    summary="Get project statistics",
    description="Get red team statistics for a project",
)
async def get_project_stats(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """Get red team statistics for a project."""
    verify_project_access(db, current_user.id, project_id)

    service = RedTeamService(db)
    stats = service.get_project_statistics(project_id)

    # Convert recent_campaigns to response models
    recent_campaigns = [
        RedTeamCampaignResponse.model_validate(c)
        for c in stats.pop("recent_campaigns", [])
    ]

    return CampaignStatsResponse(
        **stats,
        recent_campaigns=recent_campaigns,
    )
