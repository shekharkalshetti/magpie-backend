"""
Global Pydantic schemas and custom base model.

Provides a consistent base model for all Pydantic schemas in the application.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict


def datetime_to_utc_str(dt: datetime) -> str:
    """
    Convert datetime to ISO format string with UTC timezone.

    Args:
        dt: Datetime object to convert

    Returns:
        ISO formatted string with timezone
    """
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


class CustomBaseModel(BaseModel):
    """
    Custom base model with standardized configuration.

    Features:
    - Consistent datetime serialization to UTC
    - Support for ORM mode (from_attributes)
    - Helper method for serializable dict output
    """

    model_config = ConfigDict(
        json_encoders={datetime: datetime_to_utc_str},
        populate_by_name=True,
        from_attributes=True,
    )

    def serializable_dict(self, **kwargs) -> dict[str, Any]:
        """
        Return a dict containing only JSON-serializable fields.

        Useful for storing in databases or sending via APIs.
        """
        default_dict = self.model_dump(**kwargs)
        return jsonable_encoder(default_dict)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    database: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
