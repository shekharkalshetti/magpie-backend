"""
Policy database models.
"""

import copy
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base
from src.policies.constants import DEFAULT_POLICY_CONFIG


def generate_uuid() -> str:
    """Generate UUID as string."""
    return str(uuid.uuid4())


class Policy(Base):
    """
    Policy model - stores content moderation policy configuration.

    Each project can have one policy that defines:
    - Content policy compliance rules
    - Factuality & truthfulness checks
    - Security & safety measures

    The configuration is stored as JSON and can be customized per project.
    """

    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One policy per project
        index=True,
    )

    # JSON configuration storing all categories, sections, and options
    config = Column(JSON, nullable=False,
                    default=lambda: copy.deepcopy(DEFAULT_POLICY_CONFIG))

    # Whether the policy is active
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project", back_populates="policy")

    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, project_id={self.project_id}, name={self.name})>"

    def get_enabled_options(self) -> dict:
        """
        Get all enabled detection options organized by category and section.

        Returns:
            Dict with structure: {category_id: {section_id: [option_ids]}}
        """
        enabled = {}
        for category in self.config.get("categories", []):
            if not category.get("enabled", False):
                continue

            category_id = category["id"]
            enabled[category_id] = {}

            for section in category.get("sections", []):
                if not section.get("enabled", False):
                    continue

                section_id = section["id"]
                enabled_options = [
                    opt["id"]
                    for opt in section.get("options", [])
                    if opt.get("enabled", False)
                ]

                if enabled_options:
                    enabled[category_id][section_id] = enabled_options

        return enabled

    def generate_system_prompt(self) -> str:
        """
        Generate a dynamic system prompt based on enabled policy options.

        Returns:
            Formatted system prompt string for LLM content moderation.
        """
        prompt_parts = [
            "You are a content moderation system. Analyze the following content according to these policies:\n"
        ]

        for category in self.config.get("categories", []):
            if not category.get("enabled", False):
                continue

            prompt_parts.append(f"\n## {category['name']}\n")

            for section in category.get("sections", []):
                if not section.get("enabled", False):
                    continue

                enabled_options = [
                    opt["label"]
                    for opt in section.get("options", [])
                    if opt.get("enabled", False)
                ]

                if enabled_options:
                    severity = section.get("severity", "medium").upper()
                    prompt_parts.append(
                        f"\n### {section['title']} [{severity}]\n"
                        f"{section.get('policy_text', '')}\n"
                        f"Detection enabled for: {', '.join(enabled_options)}\n"
                    )

        prompt_parts.append(
            "\nFor each piece of content, identify any violations and provide:\n"
            "1. Category of violation\n"
            "2. Severity level\n"
            "3. Specific detection that triggered\n"
            "4. Recommended action (block, flag, or allow with warning)\n"
        )

        return "".join(prompt_parts)
