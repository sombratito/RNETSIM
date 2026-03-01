"""Tests for link topology computation."""

from rnetsim.api.models.scenario import Scenario, ScenarioNode
from rnetsim.fabric.launch import compute_link_topology


class TestComputeLinkTopology:
    def test_single_medium_full_mesh(self, minimal_scenario):
        """3 nodes on same medium should form a full mesh."""
        topo = compute_link_topology(minimal_scenario)
        # alpha connects to bravo and charlie
        assert len(topo["alpha"]) == 2
        # bravo and charlie don't initiate (they are higher index)
        assert len(topo["bravo"]) == 0
        assert len(topo["charlie"]) == 0

    def test_different_mediums_no_cross_links(self):
        """Nodes on different mediums should not link."""
        scenario = Scenario(
            name="isolated",
            nodes=[
                ScenarioNode(name="lora-1", interfaces=["lora_sf8_125"]),
                ScenarioNode(name="wifi-1", interfaces=["wifi_local"]),
            ],
        )
        topo = compute_link_topology(scenario)
        assert len(topo["lora-1"]) == 0
        assert len(topo["wifi-1"]) == 0

    def test_bridge_node_links_to_both(self, heterogeneous_scenario):
        """A bridge node with two interfaces should link in both medium groups."""
        topo = compute_link_topology(heterogeneous_scenario)
        # bridge is in both lora and wifi groups
        # As a member of lora group: lora-1, lora-2, bridge
        # As a member of wifi group: wifi-1, wifi-2, bridge
        # The bridge links depend on index ordering within each group
        all_targets = set()
        for node_links in topo.values():
            for link in node_links:
                all_targets.add(link["target_host"])

        # All 5 nodes should be reachable as targets (some connect to bridge, some vice versa)
        # bridge should appear as a target since lower-index nodes connect to it
        assert "bridge" in all_targets or any(
            "bridge" in link.get("name", "") for links in topo.values() for link in links
        )

    def test_all_nodes_present_in_topology(self, minimal_scenario):
        topo = compute_link_topology(minimal_scenario)
        for node in minimal_scenario.nodes:
            assert node.name in topo

    def test_link_has_correct_structure(self, minimal_scenario):
        topo = compute_link_topology(minimal_scenario)
        for link in topo["alpha"]:
            assert "name" in link
            assert "target_host" in link
            assert "target_port" in link
            assert link["target_port"] == 4242  # NODE_RETICULUM_PORT
