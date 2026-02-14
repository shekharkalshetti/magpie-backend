"""
Template storage and management system.

Handles loading, storing, and instantiating attack templates
with variable substitution.
"""
import json
import re
import random
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from src.red_teaming.models import RedTeamTemplate, AttackCategory, AttackSeverity


class TemplateVariableProcessor:
    """Processes template variables and substitutes them with values."""

    @staticmethod
    def process_variable(
        var_config: Dict[str, Any],
        provided_value: Optional[str] = None
    ) -> str:
        """
        Process a single variable based on its type.

        Args:
            var_config: Variable configuration from template
            provided_value: User-provided value (overrides default)

        Returns:
            Processed value as string
        """
        # If user provided a value, use it
        if provided_value is not None:
            return str(provided_value)

        var_type = var_config.get("type", "string")

        if var_type == "string":
            return var_config.get("default", "")

        elif var_type == "random_choice":
            choices = var_config.get("choices", [])
            if not choices:
                return var_config.get("default", "")
            return random.choice(choices)

        elif var_type == "base64_encode":
            source = var_config.get("source", var_config.get("default", ""))
            return base64.b64encode(source.encode()).decode()

        elif var_type == "rot13":
            source = var_config.get("source", var_config.get("default", ""))
            return source.translate(str.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
            ))

        elif var_type == "leetspeak":
            source = var_config.get("source", var_config.get("default", ""))
            leet_map = {'a': '4', 'e': '3', 'i': '1',
                        'o': '0', 's': '5', 't': '7'}
            return ''.join(leet_map.get(c.lower(), c) for c in source)

        else:
            return var_config.get("default", "")

    @staticmethod
    def substitute_variables(
        template_text: str,
        variables: Dict[str, Any],
        provided_values: Optional[Dict[str, str]] = None
    ) -> tuple[str, Dict[str, str]]:
        """
        Substitute all variables in template text.

        Args:
            template_text: Template with {{VARIABLE}} placeholders
            variables: Variable definitions from template
            provided_values: User-provided variable values

        Returns:
            Tuple of (instantiated_text, used_values)
        """
        provided_values = provided_values or {}
        used_values = {}

        # Find all {{VARIABLE}} patterns
        pattern = r'\{\{([A-Z_]+)\}\}'
        matches = re.findall(pattern, template_text)

        result = template_text
        for var_name in matches:
            var_config = variables.get(var_name, {})
            provided_value = provided_values.get(var_name)

            # Process the variable
            value = TemplateVariableProcessor.process_variable(
                var_config,
                provided_value
            )

            # Store the value used
            used_values[var_name] = value

            # Replace in template
            result = result.replace(f"{{{{{var_name}}}}}", value)

        return result, used_values


class TemplateLoader:
    """Loads attack templates from JSON files or database."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template loader.

        Args:
            templates_dir: Directory containing template JSON files
        """
        if templates_dir is None:
            # Default to templates directory relative to this file
            current_dir = Path(__file__).parent
            templates_dir = current_dir / "templates"

        self.templates_dir = Path(templates_dir)

    def load_from_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Load template from JSON file.

        Args:
            filepath: Path to template JSON file

        Returns:
            Template data as dictionary
        """
        with open(filepath, 'r') as f:
            return json.load(f)

    def load_all_from_directory(self) -> List[Dict[str, Any]]:
        """
        Load all templates from templates directory.

        Returns:
            List of template dictionaries
        """
        templates = []

        if not self.templates_dir.exists():
            return templates

        # Recursively find all .json files
        for filepath in self.templates_dir.rglob("*.json"):
            try:
                template = self.load_from_file(filepath)
                templates.append(template)
            except Exception as e:
                print(f"Error loading template {filepath}: {e}")

        return templates

    def seed_database(self, db: Session) -> int:
        """
        Load templates from files and seed database.

        Args:
            db: Database session

        Returns:
            Number of templates loaded
        """
        templates_data = self.load_all_from_directory()
        count = 0

        for template_data in templates_data:
            # Check if template already exists
            existing = db.query(RedTeamTemplate).filter_by(
                id=template_data.get("id")
            ).first()

            if existing:
                # Update existing template
                existing.name = template_data.get("name")
                existing.category = template_data.get("category")
                existing.severity = template_data.get("severity")
                existing.description = template_data.get("description")
                existing.template_text = template_data.get("template")
                existing.variables = template_data.get("variables", {})
                existing.expected_behavior = template_data.get(
                    "expected_behavior", {})
                existing.is_active = template_data.get("is_active", True)
            else:
                # Create new template
                template = RedTeamTemplate(
                    id=template_data.get("id"),
                    name=template_data.get("name"),
                    category=template_data.get("category"),
                    severity=template_data.get("severity"),
                    description=template_data.get("description"),
                    template_text=template_data.get("template"),
                    variables=template_data.get("variables", {}),
                    expected_behavior=template_data.get(
                        "expected_behavior", {}),
                    is_active=template_data.get("is_active", True),
                    is_custom=False
                )
                db.add(template)

            count += 1

        db.commit()
        return count


class TemplateInstantiator:
    """Instantiates attack templates with variable values."""

    def __init__(self, db: Session):
        """
        Initialize template instantiator.

        Args:
            db: Database session
        """
        self.db = db
        self.processor = TemplateVariableProcessor()

    def get_template(self, template_id: str) -> Optional[RedTeamTemplate]:
        """
        Get template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template or None if not found
        """
        return self.db.query(RedTeamTemplate).filter_by(
            id=template_id,
            is_active=True
        ).first()

    def instantiate(
        self,
        template_id: str,
        variable_values: Optional[Dict[str, str]] = None
    ) -> Optional[tuple[str, Dict[str, str], RedTeamTemplate]]:
        """
        Instantiate a template with variable values.

        Args:
            template_id: Template ID
            variable_values: Optional variable value overrides

        Returns:
            Tuple of (instantiated_prompt, used_values, template) or None if template not found
        """
        template = self.get_template(template_id)
        if not template:
            return None

        # Substitute variables
        instantiated_text, used_values = self.processor.substitute_variables(
            template.template_text,
            template.variables or {},
            variable_values
        )

        return instantiated_text, used_values, template

    def get_templates_by_category(
        self,
        categories: List[str],
        project_id: Optional[str] = None
    ) -> List[RedTeamTemplate]:
        """
        Get templates by categories.

        Args:
            categories: List of AttackCategory values
            project_id: Optional project ID for custom templates

        Returns:
            List of matching templates
        """
        query = self.db.query(RedTeamTemplate).filter(
            RedTeamTemplate.category.in_(categories),
            RedTeamTemplate.is_active == True
        )

        # Include built-in templates and project-specific custom templates
        if project_id:
            query = query.filter(
                (RedTeamTemplate.is_custom == False) |
                (RedTeamTemplate.project_id == project_id)
            )
        else:
            query = query.filter(RedTeamTemplate.is_custom == False)

        return query.all()
