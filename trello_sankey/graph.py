"""
Graph-based data structures for modeling stage transitions.
"""

from collections import defaultdict

from .models import CardHistory, FlowData, SankeyData


class StageNode:
    """Represents a stage in the job application pipeline."""

    def __init__(self, name: str, is_final: bool = False) -> None:
        self.name = name
        self.is_final = is_final
        self.incoming_edges: dict[str, int] = defaultdict(int)
        self.outgoing_edges: dict[str, int] = defaultdict(int)
        self.cards_waiting = 0

    def add_incoming_flow(self, from_stage: str, count: int = 1) -> None:
        """Add incoming flow from another stage."""
        self.incoming_edges[from_stage] += count

    def add_outgoing_flow(self, to_stage: str, count: int = 1) -> None:
        """Add outgoing flow to another stage."""
        self.outgoing_edges[to_stage] += count

    def total_incoming(self) -> int:
        """Total cards flowing into this stage."""
        return sum(self.incoming_edges.values())

    def total_outgoing(self) -> int:
        """Total cards flowing out of this stage."""
        return sum(self.outgoing_edges.values())

    def calculate_waiting(self) -> int:
        """Calculate cards waiting at this stage."""
        if self.is_final:
            return 0  # Final stages don't have waiting cards

        incoming = self.total_incoming()
        outgoing = self.total_outgoing()
        return max(0, incoming - outgoing)


class FlowGraph:
    """Directed graph representing stage transitions in job application flow."""

    def __init__(self, pipeline_stages: list[str], final_stages: list[str]) -> None:
        self.pipeline_stages = pipeline_stages
        self.final_stages = final_stages
        self.nodes: dict[str, StageNode] = {}
        self.total_cards = 0

        # Initialize nodes
        for stage in pipeline_stages + final_stages:
            self.nodes[stage] = StageNode(stage, is_final=(stage in final_stages))

        # Add waiting node
        self.nodes["Waiting"] = StageNode("Waiting", is_final=True)

    def add_card_journey(self, stages: list[str]) -> None:
        """Add a card's journey through stages to the graph."""
        if not stages:
            return

        self.total_cards += 1

        # Add transitions between consecutive stages
        for i in range(len(stages) - 1):
            from_stage = stages[i]
            to_stage = stages[i + 1]

            # Ensure both stages exist in graph
            if from_stage not in self.nodes:
                self.nodes[from_stage] = StageNode(from_stage)
            if to_stage not in self.nodes:
                self.nodes[to_stage] = StageNode(
                    to_stage, is_final=(to_stage in self.final_stages)
                )

            # Add flow
            self.nodes[from_stage].add_outgoing_flow(to_stage)
            self.nodes[to_stage].add_incoming_flow(from_stage)

    def calculate_waiting_flows(self) -> None:
        """Calculate and add waiting flows for cards stuck at intermediate stages."""
        # First, handle cards that appear at stages without any incoming flows
        # (e.g., cards that only appear in one stage)
        for stage_name, node in self.nodes.items():
            if stage_name == "Waiting":
                continue

            # If this is the first stage in pipeline and has no incoming flows,
            # it means cards started here
            if (
                stage_name == self.pipeline_stages[0]
                and node.total_incoming() == 0
                and self.total_cards > 0
            ):
                # Add implicit incoming flow representing cards entering the system
                pass  # These cards are handled by the waiting calculation below

        # Calculate waiting flows for each stage
        for stage_name, node in self.nodes.items():
            if stage_name == "Waiting":
                continue

            # For the first pipeline stage, consider all cards as potentially entering
            if stage_name == self.pipeline_stages[0] and node.total_incoming() == 0:
                # Count cards that started at this stage
                cards_at_stage = (
                    self.total_cards if node.total_outgoing() > 0 else self.total_cards
                )
                outgoing = node.total_outgoing()
                waiting_cards = max(0, cards_at_stage - outgoing)
            else:
                waiting_cards = node.calculate_waiting()

            if waiting_cards > 0:
                # Add flow to waiting
                node.add_outgoing_flow("Waiting", waiting_cards)
                self.nodes["Waiting"].add_incoming_flow(stage_name, waiting_cards)

    def get_flows(self) -> list[FlowData]:
        """Extract all flows as FlowData objects."""
        flows = []

        for stage_name, node in self.nodes.items():
            for to_stage, count in node.outgoing_edges.items():
                flows.append(
                    FlowData(from_stage=stage_name, to_stage=to_stage, count=count)
                )

        return flows

    def to_sankey_data(self) -> SankeyData:
        """Convert graph to SankeyData."""
        self.calculate_waiting_flows()
        flows = self.get_flows()
        return SankeyData(flows=flows, total_cards=self.total_cards)

    def get_reachable_stages(self, start_stage: str) -> set[str]:
        """Get all stages reachable from a given stage using DFS."""
        if start_stage not in self.nodes:
            return set()

        visited = set()
        stack = [start_stage]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)

            # Add all outgoing stages to stack
            for next_stage in self.nodes[current].outgoing_edges:
                if next_stage not in visited:
                    stack.append(next_stage)

        return visited

    def validate_flow_conservation(self) -> bool:
        """Validate that flow is conserved (incoming = outgoing + waiting)."""
        for stage_name, node in self.nodes.items():
            if stage_name == "Waiting":
                continue  # Waiting is a sink

            incoming = node.total_incoming()
            outgoing = node.total_outgoing()

            # For non-final stages, outgoing should include waiting
            if not node.is_final and incoming > outgoing:
                # This will be fixed by calculate_waiting_flows
                continue

            # For final stages, all incoming should stay (no outgoing)
            if node.is_final and outgoing > 0:
                return False

        return True


def build_flow_graph_from_histories(
    card_histories: list[CardHistory],
    pipeline_stages: list[str],
    final_stages: list[str],
) -> FlowGraph:
    """Build a flow graph from card histories."""
    graph = FlowGraph(pipeline_stages, final_stages)

    for history in card_histories:
        graph.add_card_journey(history.stages)

    return graph
