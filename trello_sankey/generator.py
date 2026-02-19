"""
Sankey diagram data generator from Trello board movements.
"""

from collections import defaultdict

from .client import TrelloClient
from .exceptions import TrelloAPIError
from .graph import build_flow_graph_from_histories
from .models import CardHistory, SankeyData


class TrelloSankeyGenerator:
    """
    Generates SankeyMATIC format data from Trello job board movements.

    Tracks job application flow through pipeline stages and handles:
    - Backward movements (ignores them as latest position is truth)
    - Cards stuck in intermediate stages (adds Waiting flows)
    - Proper flow balancing for SankeyMATIC compatibility
    """

    # Pipeline stages in logical order
    PIPELINE_STAGES = [
        "Applications",
        "Screening",
        "Technical assessment",
        "Final rounds",
        "Offers",
    ]

    # Terminal outcome states
    FINAL_STATES = ["Accepted", "Rejected", "Rejected by me", "Discriminated"]

    def __init__(self, client: TrelloClient | None = None) -> None:
        """Initialize with Trello API client."""
        self.client = client or TrelloClient()

    def _normalize_stage_name(self, stage_name: str) -> str:
        """
        Normalize Trello list names to standard pipeline stages.

        Args:
            stage_name: Raw Trello list name

        Returns:
            Normalized stage name
        """
        if not stage_name or stage_name == "Unknown":
            return "Unknown"

        stage_lower = stage_name.lower()

        # Map common patterns to pipeline stages
        stage_mappings = [
            (["apply", "application", "sent"], "Applications"),
            (["screen", "contact"], "Screening"),
            (["technical", "assessment"], "Technical assessment"),
            (["final", "rounds"], "Final rounds"),
            (["offer", "negotiation"], "Offers"),
            (["accept"], "Accepted"),
            (["reject"], "Rejected"),
        ]

        # Check for "rejected by me" first (more specific)
        if "rejected by me" in stage_lower or "reject by me" in stage_lower:
            return "Rejected by me"

        # Check other mappings
        for keywords, normalized_name in stage_mappings:
            if any(keyword in stage_lower for keyword in keywords):
                return normalized_name

        return stage_name

    def _build_card_histories(self, board_id: str) -> list[CardHistory]:
        """
        Build movement histories for all cards, handling backward movements.

        Args:
            board_id: Trello board ID

        Returns:
            List of clean card histories
        """
        # Fetch data
        lists = self.client.get_board_lists(board_id)
        cards = self.client.get_board_cards(board_id)
        actions = self.client.get_board_actions(board_id)

        list_id_to_name = {lst.id: lst.name for lst in lists}
        card_movements: dict[str, list[str]] = defaultdict(list)

        # Process actions chronologically (reverse since API returns newest first)
        for action in reversed(actions):
            if action.type == "createCard" and action.data.list:
                card_id = str(action.data.card["id"])
                list_id = action.data.list["id"]
                list_name = list_id_to_name.get(list_id, "Unknown")
                card_movements[card_id] = [list_name]

            elif (
                action.type == "updateCard"
                and action.data.listBefore
                and action.data.listAfter
            ):
                card_id = str(action.data.card["id"])
                to_list_id = action.data.listAfter["id"]
                to_list = list_id_to_name.get(to_list_id, "Unknown")

                if card_id in card_movements:
                    card_movements[card_id].append(to_list)

        # Handle cards without movement history
        for card in cards:
            if card.id not in card_movements:
                current_list = list_id_to_name.get(card.idList, "Unknown")
                card_movements[card.id] = [current_list]

        return self._clean_backward_movements(card_movements)

    def _clean_backward_movements(
        self, card_movements: dict[str, list[str]]
    ) -> list[CardHistory]:
        """
        Clean card histories by removing backward movements.

        Args:
            card_movements: Raw card movement histories

        Returns:
            List of cleaned card histories
        """
        clean_histories = []

        for card_id, full_history in card_movements.items():
            clean_history = []
            max_pipeline_index = -1

            for stage in full_history:
                normalized_stage = self._normalize_stage_name(stage)

                # Handle final states - once reached, stop processing
                if normalized_stage in self.FINAL_STATES:
                    clean_history.append(normalized_stage)
                    break

                # Handle pipeline stages
                if normalized_stage in self.PIPELINE_STAGES:
                    current_index = self.PIPELINE_STAGES.index(normalized_stage)

                    # Skip backward movements
                    if current_index < max_pipeline_index:
                        continue

                    if (
                        max_pipeline_index != -1
                        and current_index > max_pipeline_index + 1
                    ):
                        for missing_idx in range(max_pipeline_index + 1, current_index):
                            clean_history.append(self.PIPELINE_STAGES[missing_idx])

                    # Update progress and add to history
                    max_pipeline_index = current_index
                    if not clean_history or clean_history[-1] != normalized_stage:
                        clean_history.append(normalized_stage)

                # Skip unknown stages
                elif "Unknown" in normalized_stage:
                    continue

            # Ensure non-empty history
            if not clean_history:
                clean_history = ["Applications"]

            clean_histories.append(CardHistory(card_id=card_id, stages=clean_history))

        return clean_histories

    def _calculate_flows(self, clean_histories: list[CardHistory]) -> SankeyData:
        """
        Calculate stage-to-stage flows using graph-based approach.

        Args:
            clean_histories: Clean card movement histories

        Returns:
            Complete Sankey data with flows
        """
        # Build flow graph from card histories
        flow_graph = build_flow_graph_from_histories(
            clean_histories, self.PIPELINE_STAGES, self.FINAL_STATES
        )

        # Convert graph to SankeyData (automatically handles waiting flows)
        return flow_graph.to_sankey_data()

    def generate_sankeymatic_data(self, board_id: str) -> str:
        """
        Generate SankeyMATIC format data from Trello board.

        Args:
            board_id: Trello board ID

        Returns:
            Formatted data string ready for SankeyMATIC

        Raises:
            TrelloAPIError: If API requests fail
        """
        try:
            # Build clean card histories
            clean_histories = self._build_card_histories(board_id)

            if not clean_histories:
                return "No job application data found."

            # Calculate flows
            sankey_data = self._calculate_flows(clean_histories)

            if not sankey_data.flows:
                return "No flows generated from the data."

            # Format for SankeyMATIC
            sankeymatic_output = sankey_data.to_sankeymatic_string()

            print("\n--- SankeyMATIC Format Data ---")
            print(sankeymatic_output)
            print("\n--- Copy the above data to SankeyMATIC.com ---")

            return sankeymatic_output

        except Exception as e:
            raise TrelloAPIError(f"Failed to generate Sankey data: {str(e)}") from e
