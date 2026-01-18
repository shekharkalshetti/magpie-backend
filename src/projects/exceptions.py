"""
Project-specific exceptions.
"""

from src.exceptions import ConflictError, NotFoundError


class ProjectNotFoundError(NotFoundError):
    """Raised when a project is not found."""

    def __init__(self, project_id: str):
        super().__init__(resource="Project", identifier=project_id)


class ProjectNameExistsError(ConflictError):
    """Raised when a project with the same name already exists."""

    def __init__(self, name: str):
        super().__init__(detail=f"Project with name '{name}' already exists")


class MetadataKeyNotFoundError(NotFoundError):
    """Raised when a metadata key is not found."""

    def __init__(self, key: str):
        super().__init__(resource="Metadata key", identifier=key)


class MetadataKeyExistsError(ConflictError):
    """Raised when a metadata key already exists for a project."""

    def __init__(self, key: str, project_id: str):
        super().__init__(detail=f"Metadata key '{key}' already exists for project {project_id}")
