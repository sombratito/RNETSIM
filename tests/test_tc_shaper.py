"""Tests for tc/netem command generation."""

from rnetsim.fabric.link_model import get_profile
from rnetsim.fabric.tc_shaper import MIN_BURST_BYTES, generate_tc_commands


class TestGenerateTcCommands:
    def test_returns_three_commands(self):
        """Should return: delete, netem add, tbf add."""
        profile = get_profile("lora_sf8_125")
        cmds = generate_tc_commands("eth0", profile)
        assert len(cmds) == 3

    def test_first_command_cleans_existing(self):
        profile = get_profile("ethernet")
        cmds = generate_tc_commands("eth0", profile)
        assert "tc qdisc del" in cmds[0]
        assert "|| true" in cmds[0]

    def test_netem_has_delay_and_jitter(self):
        profile = get_profile("lora_sf8_125")
        cmds = generate_tc_commands("eth0", profile)
        netem_cmd = cmds[1]
        assert "netem" in netem_cmd
        assert f"delay {profile.latency} {profile.jitter}" in netem_cmd

    def test_netem_includes_loss_when_nonzero(self):
        profile = get_profile("packet_radio")  # has 2% loss
        cmds = generate_tc_commands("eth0", profile)
        netem_cmd = cmds[1]
        assert "loss 2%" in netem_cmd

    def test_netem_omits_loss_when_zero(self):
        profile = get_profile("lora_sf8_125")  # has 0% loss
        cmds = generate_tc_commands("eth0", profile)
        netem_cmd = cmds[1]
        assert "loss" not in netem_cmd

    def test_tbf_has_bandwidth(self):
        profile = get_profile("lora_sf8_125")
        cmds = generate_tc_commands("eth0", profile)
        tbf_cmd = cmds[2]
        assert "tbf" in tbf_cmd
        assert f"rate {profile.bandwidth}" in tbf_cmd

    def test_tbf_burst_minimum(self):
        """Low-bandwidth mediums should use minimum burst of 1540 bytes."""
        profile = get_profile("lora_sf12_125")
        cmds = generate_tc_commands("eth0", profile)
        tbf_cmd = cmds[2]
        assert f"burst {MIN_BURST_BYTES}" in tbf_cmd

    def test_respects_interface_name(self):
        profile = get_profile("wifi_local")
        cmds = generate_tc_commands("wlan0", profile)
        for cmd in cmds:
            assert "wlan0" in cmd
