"""
Script to add a metadata key to a project.

Usage:
    cd backend && python -m scripts.add_metadata_key \
        --project-id <PROJECT_ID> \
        --key user_id \
        --type string \
        --description "User identifier" \
        --required
    
    For enum types:
    cd backend && python -m scripts.add_metadata_key \
        --project-id <PROJECT_ID> \
        --key environment \
        --type enum \
        --enum-values dev staging prod \
        --required
"""
import argparse
import sys
import json

from src.database import SessionLocal
from src.models import MetadataKey, Project, MetadataType


def add_metadata_key(
    project_id: str,
    key: str,
    value_type: str = "string",
    description: str = None,
    required: bool = False,
    enum_values: list = None
) -> MetadataKey:
    """
    Add a metadata key to a project.

    Args:
        project_id: Project ID
        key: Metadata key name
        value_type: Type of metadata (string, int, bool, enum)
        description: Optional description
        required: Whether this key is required
        enum_values: List of allowed values for enum type

    Returns:
        Created MetadataKey instance
    """
    db = SessionLocal()

    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            print(f"Error: Project {project_id} not found", file=sys.stderr)
            sys.exit(1)

        # Validate value_type
        try:
            metadata_type = MetadataType(value_type)
        except ValueError:
            print(
                f"Error: Invalid type '{value_type}'. Must be one of: string, int, bool, enum", file=sys.stderr)
            sys.exit(1)

        # Validate enum_values for enum type
        if metadata_type == MetadataType.ENUM:
            if not enum_values or len(enum_values) == 0:
                print(f"Error: --enum-values required for enum type",
                      file=sys.stderr)
                sys.exit(1)

        # Check if key already exists
        existing = db.query(MetadataKey).filter(
            MetadataKey.project_id == project_id,
            MetadataKey.key == key
        ).first()

        if existing:
            print(
                f"Error: Metadata key '{key}' already exists for project {project_id}", file=sys.stderr)
            sys.exit(1)

        # Create metadata key
        metadata_key = MetadataKey(
            project_id=project_id,
            key=key,
            value_type=metadata_type,
            description=description,
            required=required,
            enum_values=enum_values if metadata_type == MetadataType.ENUM else None
        )

        db.add(metadata_key)
        db.commit()
        db.refresh(metadata_key)

        # Print ID to stdout for scripting
        print(metadata_key.id)

        # Print details to stderr for human readability
        print(
            f"\n✓ Added metadata key '{key}' to project '{project.name}'", file=sys.stderr)
        print(f"  ID: {metadata_key.id}", file=sys.stderr)
        print(f"  Type: {metadata_key.value_type.value}", file=sys.stderr)
        print(
            f"  Description: {metadata_key.description or 'N/A'}", file=sys.stderr)
        print(f"  Required: {metadata_key.required}", file=sys.stderr)
        if metadata_key.enum_values:
            print(
                f"  Enum values: {', '.join(metadata_key.enum_values)}", file=sys.stderr)

        return metadata_key

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Add metadata key to a project")
    parser.add_argument("--project-id", required=True, help="Project ID")
    parser.add_argument("--key", required=True, help="Metadata key name")
    parser.add_argument("--type", default="string",
                        choices=["string", "int", "bool", "enum"],
                        help="Value type (default: string)")
    parser.add_argument("--description", help="Key description")
    parser.add_argument("--required", action="store_true",
                        help="Mark as required")
    parser.add_argument("--enum-values", nargs="+",
                        help="Allowed values for enum type")

    args = parser.parse_args()

    add_metadata_key(
        args.project_id,
        args.key,
        args.type,
        args.description,
        args.required,
        args.enum_values
    )


if __name__ == "__main__":
    main()
