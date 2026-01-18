"""
Policy-related exceptions.
"""

from src.exceptions import ConflictError, NotFoundError, TritonException


class PolicyNotFoundError(NotFoundError):
    """Raised when a policy is not found."""

    def __init__(self, policy_id: str):
        super().__init__("Policy", policy_id)
        self.policy_id = policy_id


class PolicyExistsError(ConflictError):
    """Raised when trying to create a policy that already exists for a project."""

    def __init__(self, project_id: str):
        super().__init__(f"Policy already exists for project '{project_id}'")
        self.project_id = project_id


class InvalidPolicyConfigError(TritonException):
    """Raised when policy configuration is invalid."""

    def __init__(self, message: str):
        from fastapi import status
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid policy configuration: {message}",
        )
