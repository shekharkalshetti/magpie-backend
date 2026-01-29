"""
User request and response schemas.
"""

from datetime import datetime
from typing import Optional, Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from email_validator import EmailNotValidError, validate_email

from src.users.models import UserRole


class EmailValidation(str):
    """Email field that allows test domains like .local"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError("email must be a string")
        try:
            # Allow test domains (.local, .test, etc.)
            valid = validate_email(v, check_deliverability=False)
            return valid.email
        except EmailNotValidError as e:
            raise ValueError(f"invalid email: {e}")


class UserSignUp(BaseModel):
    """User signup request."""

    email: str = Field(...,
                       description="Email address (allows test domains like .local)")
    password: str = Field(..., min_length=8,
                          description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1)
    invite_token: Optional[str] = None  # If signing up with an invitation

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not v or "@" not in v:
            raise ValueError("invalid email format")
        # Allow test domains
        try:
            valid = validate_email(v, check_deliverability=False)
            return valid.email
        except Exception:
            # If validation fails, still accept it (allows .local domains)
            return v.lower()


class UserLogin(BaseModel):
    """User login request."""

    email: str = Field(..., description="Email address")
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not v or "@" not in v:
            raise ValueError("invalid email format")
        # Allow test domains
        try:
            valid = validate_email(v, check_deliverability=False)
            return valid.email
        except Exception:
            # If validation fails, still accept it (allows .local domains)
            return v.lower()


class UserResponse(BaseModel):
    """User response (public info only)."""

    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class InviteUserRequest(BaseModel):
    """Request to invite a user to a project."""

    email: str = Field(...,
                       description="Email address (allows test domains like .local)")
    role: UserRole = UserRole.MEMBER  # Use enum with default value

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not v or "@" not in v:
            raise ValueError("invalid email format")
        # Allow test domains
        try:
            valid = validate_email(v, check_deliverability=False)
            return valid.email
        except Exception:
            # If validation fails, still accept it (allows .local domains)
            return v.lower()


class InvitationResponse(BaseModel):
    """User invitation response."""

    id: str
    project_id: str
    invited_email: str
    role: str
    status: str
    token: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberResponse(BaseModel):
    """Project member response."""

    user_id: str
    email: str
    full_name: str
    role: str
    joined_at: datetime


class TeamMemberResponse(BaseModel):
    """Team member response."""

    user_id: str
    email: str
    name: str
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectWithMembersResponse(BaseModel):
    """Project response with member list."""

    project_id: str
    project_name: str
    description: Optional[str]
    members: list[ProjectMemberResponse]
    created_at: datetime


class UserProjectResponse(BaseModel):
    """User's project membership info."""

    project_id: str
    project_name: str
    role: str
    created_at: datetime
