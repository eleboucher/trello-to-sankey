"""
Configuration management for Trello API credentials.
"""

import os

from pydantic import BaseModel, Field

from .exceptions import TrelloAPIError


class TrelloConfig(BaseModel):
    """Trello API configuration."""

    api_key: str = Field(min_length=1)
    token: str = Field(min_length=1)
    base_url: str = "https://api.trello.com/1"

    @classmethod
    def from_env(cls) -> "TrelloConfig":
        """Create config from environment variables."""
        api_key = os.getenv("TRELLO_API_KEY")
        token = os.getenv("TRELLO_TOKEN")

        if not api_key or not token:
            raise TrelloAPIError(
                "Missing Trello credentials. Please set TRELLO_API_KEY and "
                "TRELLO_TOKEN environment variables."
            )

        return cls(api_key=api_key, token=token)
