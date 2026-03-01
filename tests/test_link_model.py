"""Tests for link characteristic profiles and medium validation."""

import pytest

from rnetsim.fabric.link_model import (
    PROFILES,
    VALID_MEDIUMS,
    LinkProfile,
    get_profile,
)


class TestLinkProfiles:
    def test_all_ten_mediums_present(self):
        expected = {
            "lora_sf7_125",
            "lora_sf8_125",
            "lora_sf12_125",
            "wifi_local",
            "ethernet",
            "internet",
            "packet_radio",
            "satellite",
            "halow_4mhz",
            "sneakernet",
        }
        assert set(PROFILES.keys()) == expected

    def test_valid_mediums_matches_profiles(self):
        assert VALID_MEDIUMS == set(PROFILES.keys())

    def test_get_profile_returns_correct_type(self):
        profile = get_profile("lora_sf8_125")
        assert isinstance(profile, LinkProfile)
        assert profile.medium == "lora_sf8_125"

    def test_get_profile_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown medium"):
            get_profile("nonexistent_medium")

    def test_profiles_are_frozen(self):
        profile = get_profile("ethernet")
        with pytest.raises(AttributeError):
            profile.bandwidth = "999"

    def test_lora_sf12_has_high_latency(self):
        """SF12 should have much higher latency than SF7."""
        sf7 = get_profile("lora_sf7_125")
        sf12 = get_profile("lora_sf12_125")
        # Parse latency values (e.g., "50ms" -> 50)
        sf7_ms = int(sf7.latency.replace("ms", ""))
        sf12_ms = int(sf12.latency.replace("ms", ""))
        assert sf12_ms > sf7_ms

    def test_ethernet_has_highest_bandwidth(self):
        eth = get_profile("ethernet")
        assert "gbit" in eth.bandwidth
