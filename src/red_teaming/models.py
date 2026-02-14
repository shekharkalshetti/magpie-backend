"""
Red Teaming models for adversarial testing campaigns and attacks.

Tracks red team campaigns, individual attacks, templates, and results
for security testing of LLM systems.
"""
from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship

from src.database import Base


class AttackCategory(str, PyEnum):
    """Category of red team attack."""
    JAILBREAK = "jailbreak"
    PROMPT_INJECTION = "prompt_injection"
    TOXICITY = "toxicity"
    DATA_LEAKAGE = "data_leakage"
    HALLUCINATION = "hallucination"
    OBFUSCATION = "obfuscation"
    CUSTOM = "custom"


class AttackSeverity(str, PyEnum):
    """Severity level of attack."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CampaignStatus(str, PyEnum):
    """Status of red team campaign."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(str, PyEnum):
    """Overall risk level assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RedTeamTemplate(Base):
    """
    Attack template for red teaming.

    Stores reusable attack patterns with variable placeholders
    that can be instantiated for testing.
    """
    __tablename__ = "red_team_templates"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Template metadata
    name = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)  # AttackCategory
    severity = Column(String, nullable=False)  # AttackSeverity
    description = Column(Text, nullable=True)

    # Template content
    template_text = Column(Text, nullable=False)
    # Variable definitions
    variables = Column(JSON, nullable=True, default=dict)
    # Safe vs unsafe responses
    expected_behavior = Column(JSON, nullable=True, default=dict)

    # Metadata
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    # User-created vs built-in
    is_custom = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    project_id = Column(String, ForeignKey("projects.id"),
                        nullable=True, index=True)  # If custom per-project

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    # Relationships
    attacks = relationship("RedTeamAttack", back_populates="template")


class RedTeamCampaign(Base):
    """
    Red team campaign for systematic security testing.

    Represents a coordinated effort to test LLM security using
    multiple attack templates and techniques.
    """
    __tablename__ = "red_team_campaigns"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Campaign metadata
    project_id = Column(String, ForeignKey("projects.id"),
                        nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    # List of AttackCategory
    attack_categories = Column(JSON, nullable=False, default=list)
    target_model = Column(String, nullable=True)
    attacks_per_template = Column(Integer, default=1, nullable=False)
    # Campaign fails if success rate exceeds this
    fail_threshold_percent = Column(Float, nullable=True)

    # Status
    status = Column(String, nullable=False, default="pending",
                    index=True)  # CampaignStatus

    # Results
    total_attacks = Column(Integer, default=0, nullable=False)
    successful_attacks = Column(Integer, default=0, nullable=False)
    failed_attacks = Column(Integer, default=0, nullable=False)
    # Percentage of successful attacks
    success_rate = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)  # RiskLevel

    # Execution metadata
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Audit
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    # Relationships
    attacks = relationship(
        "RedTeamAttack", back_populates="campaign", cascade="all, delete-orphan")


class RedTeamAttack(Base):
    """
    Individual red team attack execution and result.

    Records each attack attempt, the generated prompt, LLM response,
    and analysis of whether the attack succeeded.
    """
    __tablename__ = "red_team_attacks"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # References
    campaign_id = Column(String, ForeignKey(
        "red_team_campaigns.id"), nullable=False, index=True)
    template_id = Column(String, ForeignKey(
        "red_team_templates.id"), nullable=True, index=True)
    execution_log_id = Column(String, ForeignKey(
        "execution_logs.id"), nullable=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"),
                        nullable=False, index=True)

    # Attack details
    attack_type = Column(String, nullable=False, index=True)  # AttackCategory
    attack_name = Column(String, nullable=False)
    attack_prompt = Column(Text, nullable=False)
    # Variables used to instantiate template
    template_variables = Column(JSON, nullable=True, default=dict)

    # LLM Response
    llm_response = Column(Text, nullable=True)
    llm_model = Column(String, nullable=True)

    # Analysis
    # Did attack bypass defenses?
    was_successful = Column(Boolean, nullable=True, index=True)
    bypass_score = Column(Float, nullable=True)  # 0.0-1.0 confidence score
    analysis_notes = Column(Text, nullable=True)  # Why attack succeeded/failed
    # Policies that were bypassed
    flagged_policies = Column(JSON, nullable=True, default=list)

    # Integration
    review_queue_id = Column(String, ForeignKey(
        "review_queue.id"), nullable=True)  # If created review item

    # Metadata
    severity = Column(String, nullable=False)  # AttackSeverity
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow,
                        nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    # Relationships
    campaign = relationship("RedTeamCampaign", back_populates="attacks")
    template = relationship("RedTeamTemplate", back_populates="attacks")
