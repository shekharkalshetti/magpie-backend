"""
Prompt file management for SDK integration.

Handles writing system prompts to shared files that the SDK can access.
This enables fast local file reads instead of API calls for on-prem deployments.
"""

import os
from pathlib import Path
from typing import Optional

from src.policies.models import Policy


# Default shared prompts directory (configurable via env)
DEFAULT_PROMPTS_DIR = os.getenv(
    "TRITON_PROMPTS_DIR",
    str(Path(__file__).parent.parent.parent / "data" / "prompts")
)


def get_prompts_dir() -> Path:
    """Get the prompts directory, creating it if needed."""
    prompts_dir = Path(DEFAULT_PROMPTS_DIR)
    prompts_dir.mkdir(parents=True, exist_ok=True)
    return prompts_dir


def get_prompt_file_path(project_id: str) -> Path:
    """Get the path to a project's system prompt file."""
    return get_prompts_dir() / f"{project_id}.txt"


def write_system_prompt(policy: Policy) -> str:
    """
    Generate and write the system prompt to a file.

    Args:
        policy: The Policy object to generate prompt from

    Returns:
        The path to the written file
    """
    prompt_content = policy.generate_system_prompt()
    file_path = get_prompt_file_path(policy.project_id)

    # Write atomically (write to temp, then rename)
    temp_path = file_path.with_suffix(".tmp")
    temp_path.write_text(prompt_content, encoding="utf-8")
    temp_path.rename(file_path)

    return str(file_path)


def read_system_prompt(project_id: str) -> Optional[str]:
    """
    Read the system prompt from file.

    Args:
        project_id: The project ID

    Returns:
        The prompt content, or None if file doesn't exist
    """
    file_path = get_prompt_file_path(project_id)
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return None


def delete_system_prompt(project_id: str) -> bool:
    """
    Delete a project's system prompt file.

    Args:
        project_id: The project ID

    Returns:
        True if deleted, False if file didn't exist
    """
    file_path = get_prompt_file_path(project_id)
    if file_path.exists():
        file_path.unlink()
        return True
    return False


def prompt_file_exists(project_id: str) -> bool:
    """Check if a prompt file exists for a project."""
    return get_prompt_file_path(project_id).exists()
