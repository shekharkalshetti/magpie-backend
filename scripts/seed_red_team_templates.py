#!/usr/bin/env python3
"""
Seed red team templates from JSON files into the database.

This script loads all attack templates from the templates directory
and inserts them into the database for use in red team campaigns.
"""
from src.red_teaming.template_manager import TemplateLoader
from src.database import SessionLocal
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import models to ensure all tables are registered with SQLAlchemy
import src.models  # noqa: F401


def seed_templates():
    """Load and seed all red team templates into the database."""
    db = SessionLocal()

    try:
        # Find templates directory
        templates_dir = Path(__file__).parent.parent / \
            "src" / "red_teaming" / "templates"

        if not templates_dir.exists():
            print(f"❌ Templates directory not found: {templates_dir}")
            return 1

        print(f"📁 Loading templates from: {templates_dir}")

        # Create loader and seed database
        loader = TemplateLoader(templates_dir)
        count = loader.seed_database(db)

        print(f"✅ Successfully seeded {count} templates into the database")
        return 0

    except Exception as e:
        print(f"❌ Error seeding templates: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(seed_templates())
