"""Common base classes for Veneer API models."""

from pydantic import BaseModel, ConfigDict


class VeneerRequest(BaseModel):
    """Base class for all request models with flexible field handling."""

    model_config = ConfigDict(extra="allow")


class VeneerResponse(BaseModel):
    """Base class for all response models."""
