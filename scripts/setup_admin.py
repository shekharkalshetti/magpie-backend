"""
Simple script to create a default project and admin user.
Uses environment variables for configuration.
"""
import os
import sys

from src.database import SessionLocal
from src.models import Project, User
from src.users.models import ProjectUser, UserRole
from src.auth.utils import hash_password


def setup_admin():
    """Create default project and admin user."""
    db = SessionLocal()

    try:
        # Check if admin user already exists
        admin_email = os.getenv("ADMIN_EMAIL", "admin@magpie.local")
        existing_user = db.query(User).filter(
            User.email == admin_email).first()

        # Check if default project exists
        project = db.query(Project).filter(
            Project.name == "Default Project").first()

        if not project:
            # Create default project
            project = Project(
                name="Default Project",
                description="Default project for local development"
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"✓ Created default project: {project.id}")
        else:
            print(f"✓ Using existing project: {project.id}")

        if existing_user:
            # Check if user is already associated with project
            project_user = db.query(ProjectUser).filter(
                ProjectUser.user_id == existing_user.id,
                ProjectUser.project_id == project.id
            ).first()

            if not project_user:
                # Add user to project as admin
                project_user = ProjectUser(
                    project_id=project.id,
                    user_id=existing_user.id,
                    role=UserRole.ADMIN
                )
                db.add(project_user)
                db.commit()
                print(f"✓ Added existing user to project as ADMIN")

            print(f"✓ Admin user already exists: {admin_email}")
            print(f"  User ID: {existing_user.id}")
            print(f"  Project ID: {project.id}")
            return

        # Create admin user
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_user = User(
            email=admin_email,
            full_name="Admin User",
            password_hash=hash_password(admin_password),
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        # Add user to project as admin
        project_user = ProjectUser(
            project_id=project.id,
            user_id=admin_user.id,
            role=UserRole.ADMIN
        )
        db.add(project_user)
        db.commit()

        print(f"✓ Created admin user: {admin_email}")
        print(f"  User ID: {admin_user.id}")
        print(f"  Password: {admin_password}")
        print(f"  Project ID: {project.id}")
        print(f"  Role: ADMIN")
        print()
        print("You can now log in at http://localhost:3000")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    setup_admin()
