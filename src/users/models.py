"""
User and team membership database models.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base


def generate_uuid() -> str:
    """Generate UUID as string."""
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    """User roles for team projects."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base):
    """
    User account model.

    Represents a user who can log into the platform and manage projects.
    Stores hashed password for authentication.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    # Hashed password (bcrypt)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project_memberships = relationship(
        "ProjectUser",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="ProjectUser.user_id"
    )
    invitations = relationship(
        "UserInvitation",
        back_populates="invited_user",
        cascade="all, delete-orphan",
        foreign_keys="UserInvitation.invited_user_id"
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="AuditLog.user_id"
    )


class ProjectUser(Base):
    """
    Team membership model - links users to projects.

    Tracks which users are part of which projects and their role.
    Each user can have a different role in different projects.
    """

    __tablename__ = "project_users"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey(
        "projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Unique constraint: one user per project with one role
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="unique_project_user"),
    )

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    user = relationship(
        "User", back_populates="project_memberships", foreign_keys=[user_id])


class UserInvitation(Base):
    """
    User invitation model - tracks pending invitations.

    When an admin invites a user to a project, an invitation is created.
    The invited user can accept or reject it.
    """

    __tablename__ = "user_invitations"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey(
        "projects.id", ondelete="CASCADE"), nullable=False)
    invited_email = Column(String(255), nullable=False)
    invited_user_id = Column(String, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    invited_by_user_id = Column(String, ForeignKey(
        "users.id", ondelete="SET NULL"), nullable=True)
    # pending, accepted, rejected, expired
    status = Column(String(20), default="pending")
    # Temporary password for login (hashed)
    temporary_password = Column(String(255), nullable=True)
    token = Column(String(255), unique=True, nullable=False,
                   index=True)  # Unique invite token
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    invited_user = relationship(
        "User", back_populates="invitations", foreign_keys=[invited_user_id])
    invited_by_user = relationship("User", foreign_keys=[invited_by_user_id])
