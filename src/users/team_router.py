"""Team members management routes."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.auth.middleware import get_current_user_id
from src.database import get_db
from src.exceptions import HTTPException
from src.users.models import UserRole
from src.users.schemas import (
    InvitationResponse,
    InviteUserRequest,
    TeamMemberResponse,
)
from src.users.team_service import TeamMembersService

router = APIRouter(tags=["team-members"])


@router.post("/{project_id}/team/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    project_id: str,
    request: InviteUserRequest,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> InvitationResponse:
    """
    Invite a new member to a project.

    Only project admins can invite members.
    """
    # Convert string role to UserRole enum
    role = UserRole.MEMBER
    if request.role:
        role_lower = request.role.lower()
        if role_lower == "admin":
            role = UserRole.ADMIN
        elif role_lower == "viewer":
            role = UserRole.VIEWER

    invitation = TeamMembersService.invite_member(
        session=session,
        project_id=project_id,
        invited_by_user_id=current_user_id,
        invited_email=request.email,
        role=role,
    )

    return InvitationResponse.from_orm(invitation)


@router.get("/{project_id}/team/members", status_code=status.HTTP_200_OK)
async def list_members(
    project_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> List[TeamMemberResponse]:
    """
    List all members of a project.

    Any project member can view the member list.
    """
    members = TeamMembersService.list_project_members(
        session=session, project_id=project_id
    )

    return members


@router.get("/{project_id}/team/invitations", status_code=status.HTTP_200_OK)
async def list_invitations(
    project_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> List[InvitationResponse]:
    """
    List all pending invitations for a project.

    Only project admins can view pending invitations.
    """
    # Check if user is project admin
    if not TeamMembersService.is_project_admin(
        session, current_user_id, project_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Only project admins can view pending invitations",
        )

    invitations = TeamMembersService.list_pending_invitations(
        session=session, project_id=project_id
    )

    return invitations


@router.delete("/{project_id}/team/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    project_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> None:
    """
    Remove a member from a project.

    Only project admins can remove members.
    """
    TeamMembersService.remove_member(
        session=session,
        project_id=project_id,
        user_id=user_id,
        removed_by_user_id=current_user_id,
    )


@router.delete("/{project_id}/team/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    project_id: str,
    invitation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> None:
    """
    Cancel a pending invitation.

    Only project admins can cancel invitations.
    """
    TeamMembersService.cancel_invitation(
        session=session,
        invitation_id=invitation_id,
        cancelled_by_user_id=current_user_id,
    )
