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
        """Convert all flows to SankeyMATIC format string with strict vertical ordering"""

        # Define the exact top-to-bottom vertical order we want in the diagram
        node_ranks = {
            "Rejected": 0,
            "Rejected by me": 1,
            "Discriminated": 2,
            "Applications": 3,
            "Screening": 4,
            "Technical assessment": 5,
            "Final rounds": 6,
            "Offers": 7,
            "Accepted": 8,
            "Waiting": 9,
        }

        def sort_key(flow: FlowData) -> tuple[int, int]:
            # Sort primarily by where the flow starts, then by where it goes
            from_rank = node_ranks.get(flow.from_stage, 99)
            to_rank = node_ranks.get(flow.to_stage, 99)
            return (from_rank, to_rank)

        sorted_flows = sorted(self.flows, key=sort_key)

        # Build the output text
        lines = [flow.to_sankeymatic_format() for flow in sorted_flows]

        # Add visual groupings and colors
        lines.append("\n// Colors")
        lines.append(":Rejected #ff4d4d")
        lines.append(":Rejected by me #ff4d4d")
        lines.append(":Discriminated #ff4d4d")
        lines.append(":Waiting #cccccc")
        lines.append(":Accepted #4CAF50")

        return "\n".join(lines)
