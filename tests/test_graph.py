"""
Tests for graph-based flow calculation.
"""


from trello_sankey.graph import FlowGraph, StageNode, build_flow_graph_from_histories
from trello_sankey.models import CardHistory


class TestStageNode:
    """Test StageNode class."""

    def test_stage_node_creation(self):
        """Test StageNode creation."""
        node = StageNode("Applications")
        assert node.name == "Applications"
        assert not node.is_final
        assert node.total_incoming() == 0
        assert node.total_outgoing() == 0

    def test_stage_node_final(self):
        """Test final stage node."""
        node = StageNode("Accepted", is_final=True)
        assert node.name == "Accepted"
        assert node.is_final

    def test_add_flows(self):
        """Test adding flows to stage node."""
        node = StageNode("Screening")

        node.add_incoming_flow("Applications", 5)
        node.add_outgoing_flow("Technical", 3)
        node.add_outgoing_flow("Rejected", 2)

        assert node.total_incoming() == 5
        assert node.total_outgoing() == 5
        assert node.incoming_edges["Applications"] == 5
        assert node.outgoing_edges["Technical"] == 3
        assert node.outgoing_edges["Rejected"] == 2

    def test_calculate_waiting(self):
        """Test waiting calculation."""
        node = StageNode("Screening")
        node.add_incoming_flow("Applications", 10)
        node.add_outgoing_flow("Technical", 6)

        assert node.calculate_waiting() == 4

    def test_calculate_waiting_final_stage(self):
        """Test waiting calculation for final stage."""
        node = StageNode("Accepted", is_final=True)
        node.add_incoming_flow("Final", 5)

        assert node.calculate_waiting() == 0  # Final stages don't have waiting


class TestFlowGraph:
    """Test FlowGraph class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pipeline_stages = ["Applications", "Screening", "Technical"]
        self.final_stages = ["Accepted", "Rejected"]
        self.graph = FlowGraph(self.pipeline_stages, self.final_stages)

    def test_graph_initialization(self):
        """Test graph initialization."""
        assert len(self.graph.nodes) == 6  # 3 pipeline + 2 final + 1 waiting
        assert "Applications" in self.graph.nodes
        assert "Waiting" in self.graph.nodes
        assert self.graph.nodes["Accepted"].is_final
        assert not self.graph.nodes["Applications"].is_final

    def test_add_simple_journey(self):
        """Test adding a simple card journey."""
        self.graph.add_card_journey(["Applications", "Screening", "Accepted"])

        assert self.graph.total_cards == 1
        assert self.graph.nodes["Applications"].outgoing_edges["Screening"] == 1
        assert self.graph.nodes["Screening"].incoming_edges["Applications"] == 1
        assert self.graph.nodes["Screening"].outgoing_edges["Accepted"] == 1
        assert self.graph.nodes["Accepted"].incoming_edges["Screening"] == 1

    def test_add_single_stage_journey(self):
        """Test adding a single-stage journey."""
        self.graph.add_card_journey(["Applications"])

        assert self.graph.total_cards == 1
        # No outgoing flows from Applications yet
        assert self.graph.nodes["Applications"].total_outgoing() == 0

    def test_calculate_waiting_flows(self):
        """Test waiting flow calculation."""
        # Add journeys
        self.graph.add_card_journey(["Applications", "Screening", "Accepted"])
        self.graph.add_card_journey(["Applications", "Screening"])  # Stuck at screening
        self.graph.add_card_journey(["Applications"])  # Stuck at applications

        # Calculate waiting flows
        self.graph.calculate_waiting_flows()

        # Check results
        flows = self.graph.get_flows()
        flow_dict = {f"{f.from_stage}->{f.to_stage}": f.count for f in flows}

        assert flow_dict["Applications->Screening"] == 2
        assert flow_dict["Screening->Accepted"] == 1
        assert flow_dict["Applications->Waiting"] == 1  # 1 card stuck at applications
        assert flow_dict["Screening->Waiting"] == 1  # 1 card stuck at screening

    def test_to_sankey_data(self):
        """Test conversion to SankeyData."""
        self.graph.add_card_journey(["Applications", "Screening", "Accepted"])
        self.graph.add_card_journey(["Applications", "Rejected"])

        sankey_data = self.graph.to_sankey_data()

        assert sankey_data.total_cards == 2
        assert len(sankey_data.flows) > 0

        # Check specific flows exist
        flow_strings = [f.to_sankeymatic_format() for f in sankey_data.flows]
        flow_text = "\n".join(flow_strings)

        assert "Applications [1] Screening" in flow_text
        assert "Applications [1] Rejected" in flow_text
        assert "Screening [1] Accepted" in flow_text

    def test_empty_graph(self):
        """Test empty graph behavior."""
        sankey_data = self.graph.to_sankey_data()

        assert sankey_data.total_cards == 0
        assert len(sankey_data.flows) == 0


class TestBuildFlowGraphFromHistories:
    """Test build_flow_graph_from_histories function."""

    def test_build_from_histories(self):
        """Test building graph from card histories."""
        histories = [
            CardHistory(card_id="card1", stages=["Applications", "Screening", "Accepted"]),
            CardHistory(card_id="card2", stages=["Applications", "Screening", "Technical", "Rejected"]),
            CardHistory(card_id="card3", stages=["Applications"]),
        ]

        pipeline_stages = ["Applications", "Screening", "Technical"]
        final_stages = ["Accepted", "Rejected"]

        graph = build_flow_graph_from_histories(histories, pipeline_stages, final_stages)

        assert graph.total_cards == 3

        # Check flows
        sankey_data = graph.to_sankey_data()
        flow_dict = {f"{f.from_stage}->{f.to_stage}": f.count for f in sankey_data.flows}

        assert flow_dict["Applications->Screening"] == 2
        assert flow_dict["Screening->Accepted"] == 1
        assert flow_dict["Screening->Technical"] == 1
        assert flow_dict["Technical->Rejected"] == 1
        assert flow_dict["Applications->Waiting"] == 1  # card3 stuck at Applications

    def test_build_from_empty_histories(self):
        """Test building graph from empty histories."""
        histories = []
        pipeline_stages = ["Applications", "Screening"]
        final_stages = ["Accepted", "Rejected"]

        graph = build_flow_graph_from_histories(histories, pipeline_stages, final_stages)

        assert graph.total_cards == 0
        sankey_data = graph.to_sankey_data()
        assert len(sankey_data.flows) == 0
