"""
Tests for Pydantic models.
"""

from datetime import datetime

import pytest

from trello_sankey.models import (
    CardHistory,
    FlowData,
    SankeyData,
    TrelloAction,
    TrelloActionData,
    TrelloCard,
    TrelloList,
)


class TestTrelloModels:
    """Test Trello API data models."""

    def test_trello_list_creation(self):
        """Test TrelloList model creation."""
        trello_list = TrelloList(id="list1", name="Test List")
        assert trello_list.id == "list1"
        assert trello_list.name == "Test List"
        assert trello_list.closed is False

    def test_trello_card_creation(self):
        """Test TrelloCard model creation."""
        card = TrelloCard(id="card1", name="Test Card", idList="list1")
        assert card.id == "card1"
        assert card.name == "Test Card"
        assert card.idList == "list1"
        assert card.closed is False

    def test_trello_action_data_with_int_id_short(self):
        """Test TrelloActionData handles integer idShort values."""
        action_data = TrelloActionData(
            card={"id": "card1", "idShort": 7},  # Integer idShort
            list={"id": "list1", "name": "Test List"},
        )
        assert action_data.card["id"] == "card1"
        assert action_data.card["idShort"] == 7

    def test_trello_action_data_with_string_id_short(self):
        """Test TrelloActionData handles string idShort values."""
        action_data = TrelloActionData(
            card={"id": "card1", "idShort": "7"},  # String idShort
            list={"id": "list1", "name": "Test List"},
        )
        assert action_data.card["id"] == "card1"
        assert action_data.card["idShort"] == "7"

    def test_trello_action_creation(self):
        """Test TrelloAction model creation."""
        action_data = TrelloActionData(
            card={"id": "card1", "idShort": 7},
            listBefore={"id": "list1", "name": "List 1"},
            listAfter={"id": "list2", "name": "List 2"},
        )
        action = TrelloAction(
            id="action1",
            type="updateCard",
            date=datetime.now(),
            data=action_data,
        )
        assert action.id == "action1"
        assert action.type == "updateCard"
        assert action.data.card["id"] == "card1"


class TestCardHistory:
    """Test CardHistory model."""

    def test_valid_card_history(self):
        """Test valid card history creation."""
        history = CardHistory(card_id="card1", stages=["Applications", "Screening"])
        assert history.card_id == "card1"
        assert history.stages == ["Applications", "Screening"]

    def test_empty_stages_validation(self):
        """Test that empty stages list raises validation error."""
        with pytest.raises(ValueError, match="Card history cannot be empty"):
            CardHistory(card_id="card1", stages=[])


class TestFlowData:
    """Test FlowData model."""

    def test_flow_data_creation(self):
        """Test FlowData model creation."""
        flow = FlowData(from_stage="Applications", to_stage="Screening", count=5)
        assert flow.from_stage == "Applications"
        assert flow.to_stage == "Screening"
        assert flow.count == 5

    def test_flow_data_sankeymatic_format(self):
        """Test FlowData SankeyMATIC format conversion."""
        flow = FlowData(from_stage="Applications", to_stage="Screening", count=5)
        assert flow.to_sankeymatic_format() == "Applications [5] Screening"

    def test_flow_data_zero_count_validation(self):
        """Test that zero or negative count raises validation error."""
        with pytest.raises(ValueError):
            FlowData(from_stage="Applications", to_stage="Screening", count=0)

        with pytest.raises(ValueError):
            FlowData(from_stage="Applications", to_stage="Screening", count=-1)


class TestSankeyData:
    """Test SankeyData model."""

    def test_sankey_data_creation(self):
        """Test SankeyData model creation."""
        flows = [
            FlowData(from_stage="Applications", to_stage="Screening", count=5),
            FlowData(from_stage="Screening", to_stage="Technical", count=3),
        ]
        sankey = SankeyData(flows=flows, total_cards=5)
        assert len(sankey.flows) == 2
        assert sankey.total_cards == 5

    def test_sankey_data_sankeymatic_string(self):
        """Test SankeyData SankeyMATIC string conversion."""
        flows = [
            FlowData(from_stage="Screening", to_stage="Technical", count=3),
            FlowData(from_stage="Applications", to_stage="Screening", count=5),
            FlowData(from_stage="Technical", to_stage="Final", count=2),
        ]
        sankey = SankeyData(flows=flows, total_cards=5)
        result = sankey.to_sankeymatic_string()

        # Check that flows are sorted by the flow_order
        lines = result.split("\n")
        assert "Applications [5] Screening" in lines
        assert "Screening [3] Technical" in lines
        assert "Technical [2] Final" in lines

        # Applications should come first due to sorting
        assert lines[0] == "Applications [5] Screening"

    def test_sankey_data_zero_total_cards_allowed(self):
        """Test that zero total cards is now allowed."""
        flows = []
        sankey_data = SankeyData(flows=flows, total_cards=0)
        assert sankey_data.total_cards == 0
        assert len(sankey_data.flows) == 0
