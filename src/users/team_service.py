"""Team members management service."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from src.auth.utils import generate_temporary_password, hash_password
from src.users.models import ProjectUser, User, UserInvitation, UserRole


class TeamMembersService:
    """Service for managing team members and invitations."""

    @staticmethod
    def get_user_role_in_project(
        session: Session, user_id: str, project_id: str
    ) -> Optional[UserRole]:
        """Get the user's role in a project."""
        project_user = (
            session.query(ProjectUser)
            .filter(
                and_(
                    ProjectUser.user_id == user_id,
                    ProjectUser.project_id == project_id,
                )
            )
            .first()
        )
        return project_user.role if project_user else None

    @staticmethod
    def is_project_admin(session: Session, user_id: str, project_id: str) -> bool:
        """Check if user is admin of the project."""
        role = TeamMembersService.get_user_role_in_project(
            session, user_id, project_id
        )
        return role == UserRole.ADMIN

    @staticmethod
    def invite_member(
        session: Session,
        project_id: str,
        invited_by_user_id: str,
        invited_email: str,
        role: UserRole = UserRole.MEMBER,
    ) -> UserInvitation:
        """
        Create an invitation for a new team member.

        Args:
            session: Database session
            project_id: Project to invite member to
            invited_by_user_id: User ID of the person inviting
            invited_email: Email of the person being invited
            role: Role to assign to the invited member

        Returns:
            Created UserInvitation object

        Raises:
            HTTPException: If user is not project admin or email already a member
        """
        # Check if inviter is project admin
        if not TeamMembersService.is_project_admin(
            session, invited_by_user_id, project_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Only project admins can invite members",
            )

        # Check if email is already a project member
        existing_user = session.query(User).filter(
            User.email == invited_email).first()
        if existing_user:
            existing_member = (
                session.query(ProjectUser)
                .filter(
                    and_(
                        ProjectUser.user_id == existing_user.id,
                        ProjectUser.project_id == project_id,
                    )
                )
                .first()
            )
            if existing_member:
                raise HTTPException(
                    status_code=400,
                    detail=f"User {invited_email} is already a member of this project",
                )

        # Check if invitation already exists and is pending
        existing_invitation = (
            session.query(UserInvitation)
            .filter(
                and_(
                    UserInvitation.invited_email == invited_email,
                    UserInvitation.project_id == project_id,
                    UserInvitation.status == "pending",
                )
            )
            .first()
        )
        if existing_invitation:
            raise HTTPException(
                status_code=400,
                detail=f"An invitation for {invited_email} is already pending",
            )

        # Generate temporary password
        temporary_password = generate_temporary_password()
        hashed_password = hash_password(temporary_password)

        # Generate unique invite token
        invite_token = generate_temporary_password(32)

        # Create invitation (expires in 7 days)
        invitation = UserInvitation(
            project_id=project_id,
            invited_email=invited_email,
            invited_by_user_id=invited_by_user_id,
            role=role,
            temporary_password=hashed_password,
            token=invite_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        session.add(invitation)
        session.commit()
        session.refresh(invitation)

        # Print invitation info to console (for now, instead of email)
        signup_url = f"http://localhost:3000/signup?token={invite_token}"
        print(
            f"\n{'='*80}\n"
            f"[INVITATION CREATED]\n"
            f"Email: {invited_email}\n"
            f"Project ID: {project_id}\n"
            f"Invitation Token: {invite_token}\n"
            f"Signup URL: {signup_url}\n"
            f"Expires in: 7 days\n"
            f"{'='*80}\n"
        )

        return invitation

    @staticmethod
    def list_project_members(
        session: Session, project_id: str
    ) -> List[dict]:
        """
        List all members of a project.

        Returns list of dicts with user info and role.
        """
        project_users = (
            session.query(ProjectUser)
            .filter(ProjectUser.project_id == project_id)
            .options(joinedload(ProjectUser.user))
            .all()
        )

        members = []
        for pu in project_users:
            members.append(
                {
                    "user_id": pu.user_id,
                    "email": pu.user.email,
                    "name": pu.user.full_name,
                    "role": pu.role.value,
                    "joined_at": pu.created_at,
                }
            )

        return members

    @staticmethod
    def list_pending_invitations(session: Session, project_id: str) -> List[dict]:
        """
        List all pending invitations for a project.

        Returns list of pending invitations.
        """
        invitations = (
            session.query(UserInvitation)
            .filter(
                and_(
                    UserInvitation.project_id == project_id,
                    UserInvitation.status == "pending",
                    UserInvitation.expires_at > datetime.utcnow(),
                )
            )
            .options(joinedload(UserInvitation.invited_by_user))
            .all()
        )

        result = []
        for invitation in invitations:
            result.append(
                {
                    "id": invitation.id,
                    "project_id": invitation.project_id,
                    "invited_email": invitation.invited_email,
                    "role": invitation.role.value,
                    "status": invitation.status,
                    "token": invitation.token,
                    "created_at": invitation.created_at,
                    "expires_at": invitation.expires_at,
                    "accepted_at": invitation.accepted_at,
                }
            )

        return result

    @staticmethod
    def remove_member(
        session: Session, project_id: str, user_id: str, removed_by_user_id: str
    ) -> None:
        """
        Remove a member from a project.

        Args:
            session: Database session
            project_id: Project ID
            user_id: User ID to remove
            removed_by_user_id: User removing the member

        Raises:
            HTTPException: If remover is not admin or member doesn't exist
        """
        # Check if remover is project admin
        if not TeamMembersService.is_project_admin(
            session, removed_by_user_id, project_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Only project admins can remove members",
            )

        # Find and remove the member
        project_user = (
            session.query(ProjectUser)
            .filter(
                and_(
                    ProjectUser.user_id == user_id,
                    ProjectUser.project_id == project_id,
                )
            )
            .first()
        )

        if not project_user:
            raise HTTPException(
                status_code=404,
                detail="Member not found in this project",
            )

        # Prevent removing the last admin
        if project_user.role == UserRole.ADMIN:
            admin_count = (
                session.query(func.count(ProjectUser.id))
                .filter(
                    and_(
                        ProjectUser.project_id == project_id,
                        ProjectUser.role == UserRole.ADMIN,
                    )
                )
                .scalar()
            )
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove the last admin from a project",
                )

        session.delete(project_user)
        session.commit()

    @staticmethod
    def cancel_invitation(
        session: Session, invitation_id: str, cancelled_by_user_id: str
    ) -> None:
        """
        Cancel a pending invitation.

        Args:
            session: Database session
            invitation_id: Invitation ID to cancel
            cancelled_by_user_id: User cancelling the invitation

        Raises:
            HTTPException: If invitation not found or user not authorized
        """
        invitation = (
            session.query(UserInvitation)
            .filter(UserInvitation.id == invitation_id)
            .first()
        )

        if not invitation:
            raise HTTPException(
                status_code=404,
                detail="Invitation not found",
            )

        # Check if canceller is project admin
        if not TeamMembersService.is_project_admin(
            session, cancelled_by_user_id, invitation.project_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Only project admins can cancel invitations",
            )

        if invitation.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Only pending invitations can be cancelled",
            )

        invitation.status = "rejected"
        session.commit()
