"""
Script to create a new project and optionally generate an API key.

Usage:
    cd backend && python -m scripts.create_project --name "My Project" --description "Description" --generate-key
"""
import argparse
import sys
import secrets
from sqlalchemy.orm import Session

from src.database import SessionLocal, engine, Base
from src.models import Project, APIKey, User


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def create_project(name: str, description: str = None, skip_if_exists: bool = False, generate_key: bool = False) -> tuple:
    """
    Create a new project and optionally generate an API key.

    Args:
        name: Project name
        description: Optional project description
        skip_if_exists: If True, return existing project instead of failing
        generate_key: If True, also generate an API key

    Returns:
        Tuple of (Project, api_key_value) or (Project, None)
    """
    # Ensure tables exist before querying
    create_tables()

    db = SessionLocal()

    try:
        # Check if project exists
        existing = db.query(Project).filter(Project.name == name).first()
        if existing:
            if skip_if_exists:
                # Return existing project ID
                print(existing.id)
                print(f"\n✓ Using existing project '{name}'", file=sys.stderr)
                print(f"  ID: {existing.id}", file=sys.stderr)

                # Generate API key if requested
                if generate_key:
                    api_key_value = generate_api_key(db, existing)
                    return existing, api_key_value
                return existing, None
            else:
                print(
                    f"Error: Project '{name}' already exists with ID: {existing.id}", file=sys.stderr)
                sys.exit(1)

        # Create project
        project = Project(name=name, description=description)
        db.add(project)
        db.commit()
        db.refresh(project)

        # Print ID to stdout for scripting
        print(project.id)

        # Print details to stderr for human readability
        print(f"\n✓ Created project '{name}'", file=sys.stderr)
        print(f"  ID: {project.id}", file=sys.stderr)
        print(
            f"  Description: {project.description or 'N/A'}", file=sys.stderr)

        # Generate API key if requested
        api_key_value = None
        if generate_key:
            api_key_value = generate_api_key(db, project)

        return project, api_key_value

    finally:
        db.close()


def generate_api_key(db: Session, project: Project) -> str:
    """Generate an API key for the project."""
    # Get the first active user (admin)
    user = db.query(User).filter(User.is_active == True).first()
    if not user:
        print("Error: No active user found. Run setup_admin.py first.", file=sys.stderr)
        sys.exit(1)

    # Generate API key
    api_key_value = f"tr_{secrets.token_urlsafe(32)}"
    api_key = APIKey(
        key=api_key_value,
        project_id=project.id,
        user_id=user.id,
        is_active=True
    )
    db.add(api_key)
    db.commit()

    # Print API key (prefixed for parsing)
    print(f"API_KEY:{api_key_value}")
    print(f"  API Key: {api_key_value}", file=sys.stderr)

    return api_key_value


def main():
    parser = argparse.ArgumentParser(description="Create a new Triton project")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--init-db", action="store_true",
                        help="Initialize database tables")
    parser.add_argument("--skip-if-exists", action="store_true",
                        help="Use existing project if it already exists")
    parser.add_argument("--generate-key", action="store_true",
                        help="Generate an API key for the project")

    args = parser.parse_args()

    if args.init_db:
        print("Initializing database tables...", file=sys.stderr)
        create_tables()
        print("✓ Database tables created", file=sys.stderr)

    create_project(args.name, args.description,
                   args.skip_if_exists, args.generate_key)


if __name__ == "__main__":
    main()
