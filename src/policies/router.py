"""
Policy API routes.

Handles policy CRUD operations and configuration management.
"""

import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database import get_db
from src.policies import service
from src.policies.dependencies import valid_policy_id
from src.policies.exceptions import (
    InvalidPolicyConfigError,
    PolicyExistsError,
    PolicyNotFoundError,
)
from src.policies.models import Policy
from src.policies.schemas import (
    BulkToggleRequest,
    CategoryToggleRequest,
    OptionToggleRequest,
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
    SectionToggleRequest,
    SystemPromptResponse,
)
from src.audit_logs.service import AuditLogService
from src.models import AuditAction

router = APIRouter()


# ============================================================================
# Policy CRUD Endpoints
# ============================================================================


@router.post(
    "/{project_id}",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a policy for a project",
    description="Create a new policy for a project. Each project can only have one policy.",
)
async def create_policy(
    project_id: str,
    data: PolicyCreate | None = None,
    db: Session = Depends(get_db),
):
    """
    Create a new policy for a project.

    Uses default configuration if no custom config is provided.
    """
    try:
        policy = await service.create_policy(db, project_id, data)
        return PolicyResponse.from_orm_model(policy)
    except PolicyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/project/{project_id}",
    response_model=PolicyResponse,
    summary="Get policy by project ID",
    description="Get the policy for a specific project. Creates default policy if none exists.",
)
async def get_policy_by_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Get the policy for a project.

    If no policy exists, creates a default one.
    """
    policy = await service.get_or_create_policy(db, project_id)
    return PolicyResponse.from_orm_model(policy)


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Get policy by ID",
)
async def get_policy(
    policy: Policy = Depends(valid_policy_id),
):
    """Get a specific policy by its ID."""
    return PolicyResponse.from_orm_model(policy)


@router.put(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Update a policy",
    description="Update policy name, description, active status, or full configuration.",
)
async def update_policy(
    policy_id: str,
    data: PolicyUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update a policy."""
    try:
        # Get old policy for audit comparison
        old_policy = await service.get_policy(db, policy_id)
        if not old_policy:
            raise PolicyNotFoundError(policy_id)

        # Serialize old policy safely
        try:
            old_policy_dict = json.dumps({
                "id": str(old_policy.id),
                "project_id": old_policy.project_id,
                "is_active": old_policy.is_active,
                "config": old_policy.config,
            }, default=str)
        except Exception as e:
            print(f"Error serializing old policy: {e}")
            old_policy_dict = None

        # Update policy
        policy = await service.update_policy(db, policy_id, data)

        # Serialize new policy safely
        try:
            new_policy_dict = json.dumps({
                "id": str(policy.id),
                "project_id": policy.project_id,
                "is_active": policy.is_active,
                "config": policy.config,
            }, default=str)
        except Exception as e:
            print(f"Error serializing new policy: {e}")
            new_policy_dict = None

        # Log to audit logs
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    user_id=user_id,
                    project_id=policy.project_id,
                    action=AuditAction.CREATE,
                    description="Policy configuration updated",
                )
            except Exception as e:
                print(f"Error creating audit log: {e}")

        # Commit the transaction to ensure audit log is saved
        db.commit()

        return PolicyResponse.from_orm_model(policy)
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a policy",
)
async def delete_policy(
    policy_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a policy."""
    try:
        # Get policy for audit logging before deletion
        policy = await service.get_policy(db, policy_id)
        if not policy:
            raise PolicyNotFoundError(policy_id)

        try:
            policy_dict = json.dumps({
                "id": str(policy.id),
                "project_id": policy.project_id,
                "is_active": policy.is_active,
                "config": policy.config,
            }, default=str)
        except Exception as e:
            print(f"Error serializing policy for deletion: {e}")
            policy_dict = None

        # Delete policy
        await service.delete_policy(db, policy_id)

        # Log to audit logs
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    user_id=user_id,
                    project_id=policy.project_id,
                    action=AuditAction.DELETE,
                    description="Policy deleted",
                )
            except Exception as e:
                print(f"Error creating audit log for deletion: {e}")
                import traceback
                traceback.print_exc()

        # Commit the transaction to ensure audit log is saved
        db.commit()
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{policy_id}/reset",
    response_model=PolicyResponse,
    summary="Reset policy to defaults",
    description="Reset policy configuration to default values.",
)
async def reset_policy(
    policy_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Reset a policy to default configuration."""
    try:
        policy = await service.reset_policy_to_defaults(db, policy_id)

        # Log to audit logs
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    user_id=user_id,
                    project_id=policy.project_id,
                    action=AuditAction.RESET,
                    description="Policy reset to default configuration",
                )
                db.commit()
            except Exception as e:
                print(f"Error creating audit log for reset: {e}")

        return PolicyResponse.from_orm_model(policy)
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# Toggle Endpoints
# ============================================================================


@router.post(
    "/{policy_id}/toggle/category",
    response_model=PolicyResponse,
    summary="Toggle a category",
    description="Enable or disable an entire policy category.",
)
async def toggle_category(
    policy_id: str,
    data: CategoryToggleRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Toggle a category's enabled state."""
    try:
        policy = await service.toggle_category(
            db, policy_id, data.category_id, data.enabled
        )

        # Flush changes to session
        db.flush()

        # Log to audit logs
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    user_id=user_id,
                    project_id=policy.project_id,
                    action=AuditAction.UPDATE,
                    description=f"Toggled category {data.category_id} to {data.enabled}",
                )
            except Exception as e:
                print(f"Error creating audit log for toggle_category: {e}")

        # Always commit the policy changes
        db.commit()

        return PolicyResponse.from_orm_model(policy)
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidPolicyConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{policy_id}/toggle/section",
    response_model=PolicyResponse,
    summary="Toggle a section",
    description="Enable or disable a policy section within a category.",
)
async def toggle_section(
    policy_id: str,
    data: SectionToggleRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Toggle a section's enabled state."""
    try:
        policy = await service.toggle_section(
            db, policy_id, data.category_id, data.section_id, data.enabled
        )

        # Flush changes to session
        db.flush()

        # Log to audit logs
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    user_id=user_id,
                    project_id=policy.project_id,
                    action=AuditAction.UPDATE,
                    description=f"Toggled section {data.section_id} to {data.enabled}",
                )
            except Exception as e:
                print(f"Error creating audit log for toggle_section: {e}")

        # Always commit the policy changes
        db.commit()

        return PolicyResponse.from_orm_model(policy)
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidPolicyConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{policy_id}/toggle/option",
    response_model=PolicyResponse,
    summary="Toggle a detection option",
    description="Enable or disable a specific detection option.",
)
async def toggle_option(
    policy_id: str,
    data: OptionToggleRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Toggle a detection option's enabled state."""
    try:
        policy = await service.toggle_option(
            db,
            policy_id,
            data.category_id,
            data.section_id,
            data.option_id,
            data.enabled,
        )

        # Flush changes to session
        db.flush()

        # Log to audit logs
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    user_id=user_id,
                    project_id=policy.project_id,
                    action=AuditAction.UPDATE,
                    description=f"Toggled option {data.option_id} to {data.enabled}",
                )
            except Exception as e:
                print(f"Error creating audit log for toggle_option: {e}")

        # Always commit the policy changes
        db.commit()

        return PolicyResponse.from_orm_model(policy)
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidPolicyConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{policy_id}/toggle/bulk",
    response_model=PolicyResponse,
    summary="Bulk toggle operations",
    description="Perform multiple toggle operations in a single request.",
)
async def bulk_toggle(
    policy_id: str,
    data: BulkToggleRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Perform bulk toggle operations."""
    try:
        policy = await service.bulk_toggle(db, policy_id, data)

        # Flush changes to session
        db.flush()

        # Log to audit logs
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            try:
                AuditLogService.create_audit_log(
                    db=db,
                    user_id=user_id,
                    project_id=policy.project_id,
                    action=AuditAction.UPDATE,
                    description=f"Bulk toggle operation with {len(data.operations)} changes",
                )
            except Exception as e:
                print(f"Error creating audit log for bulk_toggle: {e}")

        # Always commit the policy changes
        db.commit()

        return PolicyResponse.from_orm_model(policy)
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================================
# System Prompt Generation
# ============================================================================


@router.get(
    "/{policy_id}/system-prompt",
    response_model=SystemPromptResponse,
    summary="Generate system prompt",
    description="Generate a dynamic system prompt based on enabled policy options.",
)
async def get_system_prompt(
    policy: Policy = Depends(valid_policy_id),
):
    """
    Generate a system prompt for LLM content moderation.

    The prompt is dynamically generated based on which policy options are enabled.
    """
    system_prompt = policy.generate_system_prompt()
    enabled_count = service.count_enabled_options(policy)

    return SystemPromptResponse(
        policy_id=policy.id,
        project_id=policy.project_id,
        system_prompt=system_prompt,
        enabled_options_count=enabled_count,
    )
