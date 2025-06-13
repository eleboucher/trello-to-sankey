"""
Pydantic models for Trello API data and Sankey diagram generation.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TrelloList(BaseModel):
    """Trello list data model."""

    id: str
    name: str
    closed: bool = False


class TrelloCard(BaseModel):
    """Trello card data model."""

    id: str
    name: str
    idList: str = Field(alias="idList")
    closed: bool = False


class TrelloActionData(BaseModel):
    """Trello action data model."""

    card: dict[str, str | int]
    list: dict[str, str] | None = None
    listBefore: dict[str, str] | None = None
    listAfter: dict[str, str] | None = None


class TrelloAction(BaseModel):
    """Trello action data model."""

    id: str
    type: str
    date: datetime
    data: TrelloActionData


class CardHistory(BaseModel):
    """Clean card movement history."""

    card_id: str
    stages: list[str]

    @field_validator("stages")
    @classmethod
    def stages_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Card history cannot be empty")
        return v


class FlowData(BaseModel):
    """Flow data between stages."""

    from_stage: str
    to_stage: str
    count: int = Field(gt=0)

    def to_sankeymatic_format(self) -> str:
        """Convert to SankeyMATIC format string."""
        return f"{self.from_stage} [{self.count}] {self.to_stage}"


class SankeyData(BaseModel):
    """Complete Sankey diagram data."""

    flows: list[FlowData]
    total_cards: int = Field(ge=0)

    def to_sankeymatic_string(self) -> str:
        """Convert all flows to SankeyMATIC format string."""
        flow_order = [
            "Applications",
            "Screening",
            "Technical",
            "Final",
            "Offers",
            "Accepted",
            "Rejected",
            "Waiting",
        ]

        def sort_key(flow: FlowData) -> int:
            for i, keyword in enumerate(flow_order):
                if keyword in flow.from_stage:
                    return i
            return 999

        sorted_flows = sorted(self.flows, key=sort_key)
        return "\n".join(flow.to_sankeymatic_format() for flow in sorted_flows)
