"""
Tests for TrelloClient.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from trello_sankey.client import TrelloClient
from trello_sankey.config import TrelloConfig
from trello_sankey.exceptions import TrelloAPIError


class TestTrelloClient:
    """Test TrelloClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = TrelloConfig(
            api_key="test_key",
            token="test_token",
            base_url="https://api.trello.com/1"
        )
        self.client = TrelloClient(config=self.config)

    @patch('requests.get')
    def test_make_authenticated_request_success(self, mock_get):
        """Test successful authenticated request."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response

        result = self.client._make_authenticated_request("test/endpoint")

        assert result == {"test": "data"}
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "test/endpoint" in call_args[0][0]
        assert "key=test_key" in call_args[0][0]
        assert "token=test_token" in call_args[0][0]

    @patch('requests.get')
    def test_make_authenticated_request_failure(self, mock_get):
        """Test failed authenticated request."""
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(TrelloAPIError, match="Failed to fetch test/endpoint"):
            self.client._make_authenticated_request("test/endpoint")

    @patch('requests.get')
    def test_get_board_lists_success(self, mock_get):
        """Test successful board lists retrieval."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"id": "list1", "name": "Test List 1", "closed": False},
            {"id": "list2", "name": "Test List 2", "closed": False},
        ]
        mock_get.return_value = mock_response

        result = self.client.get_board_lists("test_board")

        assert len(result) == 2
        assert result[0].id == "list1"
        assert result[0].name == "Test List 1"
        assert result[1].id == "list2"
        assert result[1].name == "Test List 2"

    @patch('requests.get')
    def test_get_board_cards_success(self, mock_get):
        """Test successful board cards retrieval."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {"id": "card1", "name": "Test Card 1", "idList": "list1", "closed": False},
            {"id": "card2", "name": "Test Card 2", "idList": "list2", "closed": False},
        ]
        mock_get.return_value = mock_response

        result = self.client.get_board_cards("test_board")

        assert len(result) == 2
        assert result[0].id == "card1"
        assert result[0].name == "Test Card 1"
        assert result[0].idList == "list1"
        assert result[1].id == "card2"
        assert result[1].name == "Test Card 2"
        assert result[1].idList == "list2"

    @patch('requests.get')
    def test_get_board_actions_success(self, mock_get):
        """Test successful board actions retrieval."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [
            {
                "id": "action1",
                "type": "createCard",
                "date": "2024-01-01T00:00:00.000Z",
                "data": {
                    "card": {"id": "card1", "idShort": 1},
                    "list": {"id": "list1", "name": "Test List"},
                },
            },
        ]
        mock_get.return_value = mock_response

        result = self.client.get_board_actions("test_board")

        assert len(result) == 1
        assert result[0].id == "action1"
        assert result[0].type == "createCard"
        assert result[0].data.card["id"] == "card1"
        assert result[0].data.list["id"] == "list1"

    @patch('requests.get')
    def test_get_board_actions_failure(self, mock_get):
        """Test failed board actions retrieval."""
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(TrelloAPIError, match="Failed to fetch board actions"):
            self.client.get_board_actions("test_board")

    def test_client_with_default_config(self):
        """Test client creation with default config from environment."""
        with patch('trello_sankey.config.TrelloConfig.from_env') as mock_from_env:
            mock_config = Mock(spec=TrelloConfig)
            mock_from_env.return_value = mock_config

            client = TrelloClient()

            assert client.config == mock_config
            mock_from_env.assert_called_once()
