"""
Script to seed an admin user for a project.

When you initialize Triton for a company, use this to create the initial admin account.

Usage:
    cd backend && python -m scripts.seed_admin_user \
        --project-id <PROJECT_ID> \
        --admin-email admin@company.com \
        --admin-name "John Doe" \
        --admin-password "secure-password"

Or run interactively:
    cd backend && python -m scripts.seed_admin_user
"""

import argparse
import sys
from getpass import getpass

from src.database import SessionLocal
from src.models import Project, User, ProjectUser, UserRole
from src.users.service import UserService
from src.auth.exceptions import AuthenticationError


def seed_admin_user(
    project_id: str,
    admin_email: str,
    admin_name: str,
    admin_password: str,
) -> None:
    """
    Create an admin user for a project.

    Args:
        project_id: Project ID to add admin to
        admin_email: Admin email
        admin_name: Admin full name
        admin_password: Admin password (plain text)
    """
    db = SessionLocal()

    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            print(f"❌ Error: Project '{project_id}' not found")
            sys.exit(1)

        print(f"\n✓ Found project: {project.name}")

        # Check if user already exists
        existing = db.query(User).filter(User.email == admin_email.lower()).first()
        if existing:
            print(f"⚠ User with email '{admin_email}' already exists")

            # Check if already admin of this project
            membership = db.query(ProjectUser).filter(
                ProjectUser.user_id == existing.id,
                ProjectUser.project_id == project_id,
            ).first()

            if membership and membership.role == UserRole.ADMIN:
                print(f"✓ User is already admin of project '{project.name}'")
                return

            # Add as admin if not already in project
            if not membership:
                membership = ProjectUser(
                    user_id=existing.id,
                    project_id=project_id,
                    role=UserRole.ADMIN,
                )
                db.add(membership)
                db.commit()
                print(f"✓ Added user as admin to project '{project.name}'")
            else:
                # Update role to admin
                membership.role = UserRole.ADMIN
                db.add(membership)
                db.commit()
                print(f"✓ Updated user role to admin for project '{project.name}'")
            return

        # Create new admin user
        try:
            user = UserService.create_user(
                db,
                email=admin_email,
                password=admin_password,
                full_name=admin_name,
            )
            print(f"✓ Created user: {user.email}")

        except AuthenticationError as e:
            print(f"❌ Error creating user: {e}")
            sys.exit(1)

        # Add user to project as admin
        try:
            membership = UserService.add_user_to_project(
                db,
                user_id=user.id,
                project_id=project_id,
                role=UserRole.ADMIN,
            )
            print(f"✓ Added user as admin to project '{project.name}'")

        except AuthenticationError as e:
            print(f"❌ Error adding user to project: {e}")
            sys.exit(1)

        print(
            f"\n✅ Successfully created admin user!\n"
            f"   Email: {admin_email}\n"
            f"   Project: {project.name}\n"
            f"   Role: Admin"
        )

    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed an admin user for a Triton project"
    )
    parser.add_argument(
        "--project-id",
        help="Project ID (required unless running interactively)",
    )
    parser.add_argument(
        "--admin-email",
        help="Admin email (required unless running interactively)",
    )
    parser.add_argument(
        "--admin-name",
        help="Admin full name (required unless running interactively)",
    )
    parser.add_argument(
        "--admin-password",
        help="Admin password (will prompt if not provided)",
    )

    args = parser.parse_args()

    # Get values from args or prompt interactively
    project_id = args.project_id
    admin_email = args.admin_email
    admin_name = args.admin_name
    admin_password = args.admin_password

    if not project_id:
        project_id = input("Enter project ID: ").strip()
    if not admin_email:
        admin_email = input("Enter admin email: ").strip()
    if not admin_name:
        admin_name = input("Enter admin full name: ").strip()
    if not admin_password:
        admin_password = getpass("Enter admin password: ")

    # Validate inputs
    if not all([project_id, admin_email, admin_name, admin_password]):
        print("❌ Error: All fields are required")
        sys.exit(1)

    # Create admin user
    seed_admin_user(project_id, admin_email, admin_name, admin_password)


if __name__ == "__main__":
    main()
