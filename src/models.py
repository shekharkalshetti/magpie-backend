"""
Central models module.

Imports all models to ensure SQLAlchemy can resolve relationships.
Import this module before using any models.
"""

# Import all models so SQLAlchemy can resolve relationships
from src.auth.models import ApiKey
from src.logs.models import ExecutionLog
from src.policies.models import Policy
from src.projects.models import MetadataKey, MetadataType, Project
from src.users.models import User, ProjectUser, UserInvitation, UserRole
from src.review_queue.models import ReviewQueue, ContentType, ReviewStatus, ModerationSeverity
from src.audit_logs.models import AuditLog, AuditAction
from src.red_teaming.models import (
    RedTeamCampaign,
    RedTeamAttack,
    RedTeamTemplate,
    AttackCategory,
    AttackSeverity,
    CampaignStatus,
    RiskLevel,
)

# Re-export all models for convenience
__all__ = [
    "ApiKey",
    "AttackCategory",
    "AttackSeverity",
    "AuditAction",
    "AuditLog",
    "CampaignStatus",
    "ContentType",
    "ExecutionLog",
    "MetadataKey",
    "MetadataType",
    "ModerationSeverity",
    "Policy",
    "Project",
    "ProjectUser",
    "RedTeamAttack",
    "RedTeamCampaign",
    "RedTeamTemplate",
    "ReviewQueue",
    "ReviewStatus",
    "RiskLevel",
    "User",
    "UserInvitation",
    "UserRole",
]
