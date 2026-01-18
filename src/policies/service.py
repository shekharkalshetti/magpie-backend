"""
Policy business logic service.

Contains core business logic for policy operations.
"""

import copy
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.policies.constants import DEFAULT_POLICY_CONFIG
from src.policies.exceptions import (
    InvalidPolicyConfigError,
    PolicyExistsError,
    PolicyNotFoundError,
)
from src.policies.models import Policy
from src.policies.prompt_file import write_system_prompt, delete_system_prompt
from src.policies.schemas import BulkToggleRequest, PolicyCreate, PolicyUpdate


async def create_policy(
    db: Session, project_id: str, data: PolicyCreate | None = None
) -> Policy:
    """
    Create a new policy for a project.

    Args:
        db: Database session
        project_id: Project ID to create policy for
        data: Optional policy creation data

    Returns:
        Created Policy object

    Raises:
        PolicyExistsError: If policy already exists for the project
    """
    # Check if policy already exists for this project
    existing = db.query(Policy).filter(Policy.project_id == project_id).first()
    if existing:
        raise PolicyExistsError(project_id)

    # Use provided config or default
    config = (
        data.config.model_dump() if data and data.config else copy.deepcopy(
            DEFAULT_POLICY_CONFIG)
    )

    policy = Policy(
        project_id=project_id,
        config=config,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    # Write system prompt to shared file for SDK access
    write_system_prompt(policy)

    return policy


async def get_policy(db: Session, policy_id: str) -> Policy | None:
    """
    Get a policy by ID.

    Args:
        db: Database session
        policy_id: Policy ID

    Returns:
        Policy if found, None otherwise
    """
    return db.query(Policy).filter(Policy.id == policy_id).first()


async def get_policy_by_project(db: Session, project_id: str) -> Policy | None:
    """
    Get the policy for a project.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Policy if found, None otherwise
    """
    return db.query(Policy).filter(Policy.project_id == project_id).first()


async def get_or_create_policy(db: Session, project_id: str) -> Policy:
    """
    Get existing policy or create default one for a project.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Policy object (existing or newly created)
    """
    policy = await get_policy_by_project(db, project_id)
    if not policy:
        policy = await create_policy(db, project_id)
    return policy


async def update_policy(db: Session, policy_id: str, data: PolicyUpdate) -> Policy:
    """
    Update a policy.

    Args:
        db: Database session
        policy_id: Policy ID
        data: Update data

    Returns:
        Updated Policy object

    Raises:
        PolicyNotFoundError: If policy not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    # Update fields if provided
    if data.is_active is not None:
        policy.is_active = data.is_active
    if data.config is not None:
        policy.config = data.config.model_dump()

    db.commit()
    db.refresh(policy)

    # Update system prompt file for SDK
    write_system_prompt(policy)

    return policy


async def update_policy_config(
    db: Session, policy_id: str, config: dict[str, Any]
) -> Policy:
    """
    Update policy configuration directly.

    Args:
        db: Database session
        policy_id: Policy ID
        config: New configuration

    Returns:
        Updated Policy object

    Raises:
        PolicyNotFoundError: If policy not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    policy.config = config
    flag_modified(policy, "config")
    db.commit()
    db.refresh(policy)

    # Update system prompt file for SDK
    write_system_prompt(policy)

    return policy


async def toggle_category(
    db: Session, policy_id: str, category_id: str, enabled: bool
) -> Policy:
    """
    Toggle a category's enabled state.

    Args:
        db: Database session
        policy_id: Policy ID
        category_id: Category ID to toggle
        enabled: New enabled state

    Returns:
        Updated Policy object

    Raises:
        PolicyNotFoundError: If policy not found
        InvalidPolicyConfigError: If category not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    # Find and update category
    config = policy.config
    category_found = False

    for category in config.get("categories", []):
        if category["id"] == category_id:
            category["enabled"] = enabled
            category_found = True
            break

    if not category_found:
        raise InvalidPolicyConfigError(f"Category '{category_id}' not found")

    policy.config = config
    flag_modified(policy, "config")
    # Don't commit here - let the router handle transaction with audit logging
    # db.commit()
    # db.refresh(policy)

    # Update system prompt file for SDK
    write_system_prompt(policy)

    return policy


async def toggle_section(
    db: Session, policy_id: str, category_id: str, section_id: str, enabled: bool
) -> Policy:
    """
    Toggle a section's enabled state.

    Args:
        db: Database session
        policy_id: Policy ID
        category_id: Category ID
        section_id: Section ID to toggle
        enabled: New enabled state

    Returns:
        Updated Policy object

    Raises:
        PolicyNotFoundError: If policy not found
        InvalidPolicyConfigError: If section not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    config = policy.config
    section_found = False

    for category in config.get("categories", []):
        if category["id"] == category_id:
            for section in category.get("sections", []):
                if section["id"] == section_id:
                    section["enabled"] = enabled
                    section_found = True
                    break
            break

    if not section_found:
        raise InvalidPolicyConfigError(
            f"Section '{section_id}' not found in category '{category_id}'"
        )

    policy.config = config
    flag_modified(policy, "config")
    # Don't commit here - let the router handle transaction with audit logging
    # db.commit()
    # db.refresh(policy)

    # Update system prompt file for SDK
    write_system_prompt(policy)

    return policy


async def toggle_option(
    db: Session,
    policy_id: str,
    category_id: str,
    section_id: str,
    option_id: str,
    enabled: bool,
) -> Policy:
    """
    Toggle a detection option's enabled state.

    Args:
        db: Database session
        policy_id: Policy ID
        category_id: Category ID
        section_id: Section ID
        option_id: Option ID to toggle
        enabled: New enabled state

    Returns:
        Updated Policy object

    Raises:
        PolicyNotFoundError: If policy not found
        InvalidPolicyConfigError: If option not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    config = policy.config
    option_found = False

    for category in config.get("categories", []):
        if category["id"] == category_id:
            for section in category.get("sections", []):
                if section["id"] == section_id:
                    for option in section.get("options", []):
                        if option["id"] == option_id:
                            option["enabled"] = enabled
                            option_found = True
                            break
                    break
            break

    if not option_found:
        raise InvalidPolicyConfigError(
            f"Option '{option_id}' not found in section '{section_id}'"
        )

    policy.config = config
    flag_modified(policy, "config")
    # Don't commit here - let the router handle transaction with audit logging
    # db.commit()
    # db.refresh(policy)

    # Update system prompt file for SDK
    write_system_prompt(policy)

    return policy


async def bulk_toggle(db: Session, policy_id: str, data: BulkToggleRequest) -> Policy:
    """
    Perform bulk toggle operations on policy configuration.

    Args:
        db: Database session
        policy_id: Policy ID
        data: Bulk toggle request with categories, sections, and options

    Returns:
        Updated Policy object

    Raises:
        PolicyNotFoundError: If policy not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    config = policy.config

    # Toggle categories
    if data.categories:
        for cat_toggle in data.categories:
            for category in config.get("categories", []):
                if category["id"] == cat_toggle.category_id:
                    category["enabled"] = cat_toggle.enabled
                    break

    # Toggle sections
    if data.sections:
        for sec_toggle in data.sections:
            for category in config.get("categories", []):
                if category["id"] == sec_toggle.category_id:
                    for section in category.get("sections", []):
                        if section["id"] == sec_toggle.section_id:
                            section["enabled"] = sec_toggle.enabled
                            break
                    break

    # Toggle options
    if data.options:
        for opt_toggle in data.options:
            for category in config.get("categories", []):
                if category["id"] == opt_toggle.category_id:
                    for section in category.get("sections", []):
                        if section["id"] == opt_toggle.section_id:
                            for option in section.get("options", []):
                                if option["id"] == opt_toggle.option_id:
                                    option["enabled"] = opt_toggle.enabled
                                    break
                            break
                    break

    policy.config = config
    flag_modified(policy, "config")
    # Don't commit here - let the router handle transaction with audit logging
    # db.commit()
    # db.refresh(policy)

    # Update system prompt file for SDK
    write_system_prompt(policy)

    return policy


async def delete_policy(db: Session, policy_id: str) -> None:
    """
    Delete a policy.

    Args:
        db: Database session
        policy_id: Policy ID to delete

    Raises:
        PolicyNotFoundError: If policy not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    project_id = policy.project_id
    db.delete(policy)
    db.commit()

    # Remove the system prompt file
    delete_system_prompt(project_id)


async def reset_policy_to_defaults(db: Session, policy_id: str) -> Policy:
    """
    Reset a policy to default configuration.

    Args:
        db: Database session
        policy_id: Policy ID to reset

    Returns:
        Reset Policy object

    Raises:
        PolicyNotFoundError: If policy not found
    """
    policy = await get_policy(db, policy_id)
    if not policy:
        raise PolicyNotFoundError(policy_id)

    policy.config = copy.deepcopy(DEFAULT_POLICY_CONFIG)
    db.commit()
    db.refresh(policy)

    # Update system prompt file for SDK
    write_system_prompt(policy)

    return policy


def count_enabled_options(policy: Policy) -> int:
    """
    Count total number of enabled detection options.

    Args:
        policy: Policy object

    Returns:
        Count of enabled options
    """
    count = 0
    for category in policy.config.get("categories", []):
        if not category.get("enabled", False):
            continue
        for section in category.get("sections", []):
            if not section.get("enabled", False):
                continue
            for option in section.get("options", []):
                if option.get("enabled", False):
                    count += 1
    return count
