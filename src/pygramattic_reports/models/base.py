"""Base model and utility functions for pygramattic-reports models."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


class PygramatticModel(BaseModel):
    """Base model for all pygramattic-reports data structures.

    Provides immutable, strict-mode Pydantic configuration that all
    domain models inherit from.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
    )


def generate_id() -> str:
    """Generate a unique identifier.

    Returns:
        A UUID4 string.
    """
    return str(uuid4())


def now_utc() -> datetime:
    """Generate a timezone-aware UTC timestamp.

    Returns:
        The current UTC datetime.
    """
    return datetime.now(tz=UTC)
