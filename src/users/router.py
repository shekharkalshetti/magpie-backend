"""
User authentication routes.

Handles:
- User signup
- User login
- Token refresh
- Password reset
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from src.database import get_db
from src.auth.utils import generate_jwt_token, verify_jwt_token
from src.auth.exceptions import AuthenticationError
from src.users.service import UserService
from src.users.schemas import (
    UserSignUp,
    UserLogin,
    TokenResponse,
    UserResponse,
)
from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# Dependency to extract current user from JWT token
async def get_current_user_from_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Extract and validate the current user from JWT token.

    This is used as a dependency for protected endpoints.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = parts[1]

    # Verify JWT token
    payload = verify_jwt_token(token, settings.SECRET_KEY)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Get user from database
    user = UserService.get_user_by_id(db, payload.get("user_id"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
    description="Register a new user with email and password. Optionally provide an invite token to join a project.",
)
async def signup(
    request: UserSignUp,
    db: Session = Depends(get_db),
):
    """
    Create a new user account and return an authentication token.

    If an invite token is provided, the user will be added to that project.
    The email must match the invitation email.
    """
    try:
        # If invite token provided, validate it first using service layer
        if request.invite_token:
            UserService.validate_invitation_for_signup(
                db,
                invite_token=request.invite_token,
                email=request.email,
            )

        # Create user
        user = UserService.create_user(
            db,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )

        # If invitation token provided, accept it
        if request.invite_token:
            try:
                UserService.accept_invitation(
                    db,
                    invite_token=request.invite_token,
                    user_id=user.id,
                )
            except AuthenticationError as e:
                # Log warning but don't fail signup
                logger.warning(f"Failed to accept invitation: {e}")

        # Generate JWT token
        token = generate_jwt_token(
            user_id=user.id,
            email=user.email,
            secret_key=settings.SECRET_KEY,
        )

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate a user with email and password.",
)
async def login(
    request: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT token.

    The token can be used to access protected endpoints.
    """
    try:
        # Authenticate user
        user = UserService.authenticate_user(
            db,
            email=request.email,
            password=request.password,
        )

        # Generate JWT token
        token = generate_jwt_token(
            user_id=user.id,
            email=user.email,
            secret_key=settings.SECRET_KEY,
        )

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the authenticated user's profile.",
)
async def get_current_user(
    current_user: UserResponse = Depends(get_current_user_from_token),
):
    """
    Get the currently authenticated user's profile.

    Requires a valid JWT token in the Authorization header.
    """
    return current_user
