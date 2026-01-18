"""
Script to generate an API key for a project.

Usage:
    cd backend && python -m scripts.generate_api_key \
        --project-id <PROJECT_ID> \
        --name "Production Key"
"""
import argparse
import sys

from src.database import SessionLocal
from src.models import ApiKey, Project
from src.auth.utils import generate_api_key, hash_api_key, get_key_prefix


def create_api_key(project_id: str, name: str = None) -> ApiKey:
    """
    Create an API key for a project.

    Args:
        project_id: Project ID
        name: Optional human-readable name for the key

    Returns:
        Created ApiKey instance with plaintext key
    """
    db = SessionLocal()

    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            print(f"Error: Project {project_id} not found", file=sys.stderr)
            sys.exit(1)

        # Generate API key
        key_string = generate_api_key()
        key_hash_value = hash_api_key(key_string)
        key_prefix_value = get_key_prefix(key_string)

        # Create API key record
        api_key = ApiKey(
            project_id=project_id,
            key_hash=key_hash_value,
            key_prefix=key_prefix_value,
            name=name,
            is_active=True
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        # Print to stdout for scripting
        print(key_string)

        # Print details to stderr for human readability
        print(
            f"\n✓ Generated API key for project '{project.name}'", file=sys.stderr)
        print(f"  ID: {api_key.id}", file=sys.stderr)
        print(f"  Name: {api_key.name or 'N/A'}", file=sys.stderr)
        print(f"  Prefix: {api_key.key_prefix}", file=sys.stderr)
        print(f"\n  ⚠️  Save this key securely - it won't be shown again!",
              file=sys.stderr)

        return api_key

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate API key for a project")
    parser.add_argument("--project-id", required=True, help="Project ID")
    parser.add_argument("--name", help="Human-readable name for the key")

    args = parser.parse_args()

    create_api_key(args.project_id, args.name)


if __name__ == "__main__":
    main()
