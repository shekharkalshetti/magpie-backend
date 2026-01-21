"""
API Key business logic service.

Contains core business logic for API key operations.
"""

from sqlalchemy.orm import Session

from src.auth.models import ApiKey
from src.auth.schemas import ApiKeyCreate
from src.auth.utils import generate_api_key, hash_api_key, get_key_prefix
from src.models import Project


async def list_api_keys(db: Session, project_id: str) -> list[ApiKey]:
    """
    List all API keys for a project.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        List of ApiKey objects
    """
    return db.query(ApiKey).filter(ApiKey.project_id == project_id).all()


async def create_api_key(
    db: Session, project_id: str, data: ApiKeyCreate
) -> tuple[ApiKey, str]:
    """
    Create a new API key for a project.

    Args:
        db: Database session
        project_id: Project ID
        data: API key creation data

    Returns:
        Tuple of (ApiKey object, plaintext key string)
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")

    # Generate API key
    key_string = generate_api_key()
    key_hash_value = hash_api_key(key_string)
    key_prefix_value = get_key_prefix(key_string)

    # Create API key record
    api_key = ApiKey(
        project_id=project_id,
        key_hash=key_hash_value,
        key_prefix=key_prefix_value,
        name=data.name,
        is_active=True,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key, key_string


async def delete_api_key(db: Session, project_id: str, key_id: str) -> None:
    """
    Delete an API key.

    Args:
        db: Database session
        project_id: Project ID (for verification)
        key_id: API key ID to delete
    """
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.project_id == project_id)
        .first()
    )

    if not api_key:
        raise ValueError(
            f"API key {key_id} not found for project {project_id}")

    db.delete(api_key)
    db.commit()
