"""
Trello API client for fetching board data.
"""

from typing import Any

import requests

from .config import TrelloConfig
from .exceptions import TrelloAPIError
from .models import TrelloAction, TrelloCard, TrelloList


class TrelloClient:
    """Client for interacting with the Trello API."""

    def __init__(self, config: TrelloConfig | None = None) -> None:
        """Initialize with Trello API credentials."""
        self.config = config or TrelloConfig.from_env()

    def _make_authenticated_request(self, endpoint: str) -> dict[str, Any]:
        """
        Make authenticated request to Trello API.

        Args:
            endpoint: API endpoint path (without base URL)

        Returns:
            JSON response data

        Raises:
            TrelloAPIError: If request fails
        """
        url = (
            f"{self.config.base_url}/{endpoint}/"
            f"?key={self.config.api_key}&token={self.config.token}"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except requests.RequestException as e:
            raise TrelloAPIError(f"Failed to fetch {endpoint}: {str(e)}") from e

    def get_board_lists(self, board_id: str) -> list[TrelloList]:
        """Get all lists for a board."""
        lists_data = self._make_authenticated_request(f"boards/{board_id}/lists")
        return [TrelloList.model_validate(lst) for lst in lists_data]

    def get_board_cards(self, board_id: str) -> list[TrelloCard]:
        """Get all cards for a board."""
        cards_data = self._make_authenticated_request(f"boards/{board_id}/cards")
        return [TrelloCard.model_validate(card) for card in cards_data]

    def get_board_actions(self, board_id: str) -> list[TrelloAction]:
        """
        Get board actions for card movements.

        Args:
            board_id: Trello board ID

        Returns:
            List of validated action objects
        """
        url = (
            f"{self.config.base_url}/boards/{board_id}/actions"
            f"?key={self.config.api_key}&token={self.config.token}"
            f"&filter=updateCard:idList,createCard&limit=1000"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            actions_data = response.json()
            return [TrelloAction(**action) for action in actions_data]
        except requests.RequestException as e:
            raise TrelloAPIError(f"Failed to fetch board actions: {str(e)}") from e
