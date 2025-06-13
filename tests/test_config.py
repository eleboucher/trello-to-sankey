"""
Tests for configuration module.
"""

from unittest.mock import patch

import pytest

from trello_sankey.config import TrelloConfig
from trello_sankey.exceptions import TrelloAPIError


class TestTrelloConfig:
    """Test TrelloConfig class."""

    def test_config_creation(self):
        """Test TrelloConfig creation."""
        config = TrelloConfig(
            api_key="test_key",
            token="test_token",
        )
        assert config.api_key == "test_key"
        assert config.token == "test_token"
        assert config.base_url == "https://api.trello.com/1"

    def test_config_custom_base_url(self):
        """Test TrelloConfig with custom base URL."""
        config = TrelloConfig(
            api_key="test_key",
            token="test_token",
            base_url="https://custom.api.com/v1",
        )
        assert config.base_url == "https://custom.api.com/v1"

    def test_config_validation_empty_api_key(self):
        """Test TrelloConfig validation with empty API key."""
        with pytest.raises(ValueError):
            TrelloConfig(api_key="", token="test_token")

    def test_config_validation_empty_token(self):
        """Test TrelloConfig validation with empty token."""
        with pytest.raises(ValueError):
            TrelloConfig(api_key="test_key", token="")

    @patch('os.getenv')
    def test_from_env_success(self, mock_getenv):
        """Test successful config creation from environment."""
        mock_getenv.side_effect = lambda key: {
            "TRELLO_API_KEY": "env_api_key",
            "TRELLO_TOKEN": "env_token",
        }.get(key)

        config = TrelloConfig.from_env()

        assert config.api_key == "env_api_key"
        assert config.token == "env_token"
        assert config.base_url == "https://api.trello.com/1"

    @patch('os.getenv')
    def test_from_env_missing_api_key(self, mock_getenv):
        """Test config creation from environment with missing API key."""
        mock_getenv.side_effect = lambda key: {
            "TRELLO_API_KEY": None,
            "TRELLO_TOKEN": "env_token",
        }.get(key)

        with pytest.raises(TrelloAPIError, match="Missing Trello credentials"):
            TrelloConfig.from_env()

    @patch('os.getenv')
    def test_from_env_missing_token(self, mock_getenv):
        """Test config creation from environment with missing token."""
        mock_getenv.side_effect = lambda key: {
            "TRELLO_API_KEY": "env_api_key",
            "TRELLO_TOKEN": None,
        }.get(key)

        with pytest.raises(TrelloAPIError, match="Missing Trello credentials"):
            TrelloConfig.from_env()

    @patch('os.getenv')
    def test_from_env_missing_both(self, mock_getenv):
        """Test config creation from environment with missing credentials."""
        mock_getenv.return_value = None

        with pytest.raises(TrelloAPIError, match="Missing Trello credentials"):
            TrelloConfig.from_env()
