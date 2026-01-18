"""
User management and authentication service.

Handles:
- User registration and authentication
- Password verification
- Team membership management
- User invitations
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from src.users.models import User, ProjectUser, UserInvitation, UserRole
from src.auth.utils import hash_password, verify_password, generate_invite_token
from src.auth.exceptions import AuthenticationError
from src.projects.models import Project


class UserService:
    """Service for user management operations."""

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        full_name: str,
    ) -> User:
        """
        Create a new user account.

        Args:
            db: Database session
            email: User email (must be unique)
            password: Plain text password (will be hashed)
            full_name: User's full name

        Returns:
            Created User instance

        Raises:
            AuthenticationError: If email already exists
        """
        # Check if user already exists
        existing = db.query(User).filter(User.email == email.lower()).first()
        if existing:
            raise AuthenticationError("User with this email already exists")

        # Create new user
        user = User(
            email=email.lower(),
            full_name=full_name,
            password_hash=hash_password(password),
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
    ) -> User:
        """
        Authenticate a user by email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            User instance if credentials are valid

        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = db.query(User).filter(User.email == email.lower()).first()

        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User instance or None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            db: Database session
            email: User email

        Returns:
            User instance or None
        """
        return db.query(User).filter(User.email == email.lower()).first()

    @staticmethod
    def add_user_to_project(
        db: Session,
        user_id: str,
        project_id: str,
        role: UserRole = UserRole.MEMBER,
    ) -> ProjectUser:
        """
        Add a user to a project with a specific role.

        Args:
            db: Database session
            user_id: User ID
            project_id: Project ID
            role: User role in the project (default: MEMBER)

        Returns:
            Created ProjectUser instance

        Raises:
            AuthenticationError: If user/project not found or user already in project
        """
        # Verify user and project exist
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("User not found")

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise AuthenticationError("Project not found")

        # Check if user already in project
        existing = db.query(ProjectUser).filter(
            ProjectUser.user_id == user_id,
            ProjectUser.project_id == project_id,
        ).first()
        if existing:
            raise AuthenticationError("User is already a member of this project")

        # Create project user membership
        project_user = ProjectUser(
            user_id=user_id,
            project_id=project_id,
            role=role,
        )

        db.add(project_user)
        db.commit()
        db.refresh(project_user)
        return project_user

    @staticmethod
    def invite_user_to_project(
        db: Session,
        project_id: str,
        invited_email: str,
        invited_by_user_id: str,
        role: UserRole = UserRole.MEMBER,
        expires_in_days: int = 7,
    ) -> UserInvitation:
        """
        Invite a user to a project.

        If the user already has an account, they will be added directly.
        Otherwise, an invitation is created and they can sign up and accept.

        Args:
            db: Database session
            project_id: Project ID
            invited_email: Email of user to invite
            invited_by_user_id: User ID of the person sending the invitation
            role: Role to assign (default: MEMBER)
            expires_in_days: Invitation expiration time (default: 7 days)

        Returns:
            Created UserInvitation instance

        Raises:
            AuthenticationError: If project or inviter not found
        """
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise AuthenticationError("Project not found")

        # Verify inviter exists and is an admin
        inviter = db.query(User).filter(User.id == invited_by_user_id).first()
        if not inviter:
            raise AuthenticationError("Inviter not found")

        # Check if inviter is admin of the project
        membership = db.query(ProjectUser).filter(
            ProjectUser.user_id == invited_by_user_id,
            ProjectUser.project_id == project_id,
        ).first()

        if not membership or membership.role != UserRole.ADMIN:
            raise AuthenticationError(
                "Only project admins can invite users"
            )

        # Check if invited user already exists
        existing_user = db.query(User).filter(
            User.email == invited_email.lower()
        ).first()

        if existing_user:
            # If user exists, add them directly to the project
            return UserService.add_user_to_project(
                db, existing_user.id, project_id, role
            )

        # Create invitation for new user
        invite_token = generate_invite_token()
        invitation = UserInvitation(
            project_id=project_id,
            invited_email=invited_email.lower(),
            invited_user_id=None,  # Will be set when user signs up
            role=role,
            invited_by_user_id=invited_by_user_id,
            token=invite_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
        )

        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def accept_invitation(
        db: Session,
        invite_token: str,
        user_id: str,
    ) -> ProjectUser:
        """
        Accept a user invitation and add user to project.

        Args:
            db: Database session
            invite_token: Invitation token
            user_id: ID of user accepting the invitation

        Returns:
            Created ProjectUser instance

        Raises:
            AuthenticationError: If invitation not found, expired, or invalid
        """
        invitation = db.query(UserInvitation).filter(
            UserInvitation.token == invite_token
        ).first()

        if not invitation:
            raise AuthenticationError("Invitation not found")

        if invitation.status != "pending":
            raise AuthenticationError(f"Invitation is {invitation.status}")

        if invitation.expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Invitation has expired")

        # Get user and verify it matches invitation email
        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.email != invitation.invited_email:
            raise AuthenticationError("User email does not match invitation")

        # Add user to project
        project_user = UserService.add_user_to_project(
            db,
            user_id,
            invitation.project_id,
            invitation.role,
        )

        # Mark invitation as accepted
        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)
        invitation.invited_user_id = user_id
        db.add(invitation)
        db.commit()

        return project_user

    @staticmethod
    def get_user_projects(
        db: Session,
        user_id: str,
    ) -> list[dict]:
        """
        Get all projects a user is a member of.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of project dicts with membership info
        """
        memberships = (
            db.query(ProjectUser)
            .filter(ProjectUser.user_id == user_id)
            .all()
        )

        projects = []
        for membership in memberships:
            projects.append({
                "project_id": membership.project.id,
                "project_name": membership.project.name,
                "role": membership.role.value,
                "created_at": membership.created_at,
            })

        return projects

    @staticmethod
    def get_project_members(
        db: Session,
        project_id: str,
    ) -> list[dict]:
        """
        Get all members of a project.

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            List of member dicts
        """
        members = (
            db.query(ProjectUser)
            .filter(ProjectUser.project_id == project_id)
            .all()
        )

        result = []
        for member in members:
            result.append({
                "user_id": member.user.id,
                "email": member.user.email,
                "full_name": member.user.full_name,
                "role": member.role.value,
                "joined_at": member.created_at,
            })

        return result
