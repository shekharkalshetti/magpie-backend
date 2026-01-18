"""
Script to create a new project.

Usage:
    cd backend && python -m scripts.create_project --name "My Project" --description "Description"
"""
import argparse
import sys
from sqlalchemy.orm import Session

from src.database import SessionLocal, engine, Base
from src.models import Project


def create_tables():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def create_project(name: str, description: str = None, skip_if_exists: bool = False) -> Project:
    """
    Create a new project.

    Args:
        name: Project name
        description: Optional project description
        skip_if_exists: If True, return existing project instead of failing

    Returns:
        Created Project instance
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
                return existing
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

        return project

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create a new Triton project")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--description", help="Project description")
    parser.add_argument("--init-db", action="store_true",
                        help="Initialize database tables")
    parser.add_argument("--skip-if-exists", action="store_true",
                        help="Use existing project if it already exists")

    args = parser.parse_args()

    if args.init_db:
        print("Initializing database tables...", file=sys.stderr)
        create_tables()
        print("✓ Database tables created", file=sys.stderr)

    create_project(args.name, args.description, args.skip_if_exists)


if __name__ == "__main__":
    main()
