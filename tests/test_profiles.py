"""Tests for device profile models and built-in profiles."""

from rnetsim.api.models.profile import (
    BUILTIN_PROFILE_MAP,
    BUILTIN_PROFILES,
    DeviceProfile,
)


class TestBuiltinProfiles:
    def test_nine_profiles_defined(self):
        assert len(BUILTIN_PROFILES) == 9

    def test_all_profiles_have_required_fields(self):
        for p in BUILTIN_PROFILES:
            assert p.id, f"Profile missing id"
            assert p.name, f"Profile {p.id} missing name"
            assert p.abbreviation, f"Profile {p.id} missing abbreviation"
            assert p.color.startswith("#"), f"Profile {p.id} color not hex"
            assert p.medium, f"Profile {p.id} missing medium"

    def test_profile_map_matches_list(self):
        assert len(BUILTIN_PROFILE_MAP) == len(BUILTIN_PROFILES)
        for p in BUILTIN_PROFILES:
            assert p.id in BUILTIN_PROFILE_MAP
            assert BUILTIN_PROFILE_MAP[p.id] is p

    def test_all_builtin_flag_true(self):
        for p in BUILTIN_PROFILES:
            assert p.built_in is True

    def test_unique_ids(self):
        ids = [p.id for p in BUILTIN_PROFILES]
        assert len(ids) == len(set(ids))

    def test_unique_abbreviations(self):
        abbrevs = [p.abbreviation for p in BUILTIN_PROFILES]
        assert len(abbrevs) == len(set(abbrevs))

    def test_known_profiles_exist(self):
        expected_ids = {
            "edge-c2",
            "field-node",
            "halow-bridge",
            "solar-sensor",
            "hilltop-relay",
            "roaming-relay",
            "packet-radio-tnc",
            "internet-backhaul",
            "sneakernet-courier",
        }
        actual_ids = {p.id for p in BUILTIN_PROFILES}
        assert expected_ids == actual_ids


class TestDeviceProfileModel:
    def test_custom_profile_creation(self):
        p = DeviceProfile(
            id="custom-1",
            name="Custom Device",
            abbreviation="CD",
            color="#ff0000",
            cpu="2x A53",
            ram="1 GB",
            radio="LoRa SF8",
            bandwidth_display="3.1 kbps",
            medium="lora_sf8_125",
            built_in=False,
        )
        assert p.built_in is False
        assert p.role == "endpoint"  # default
        assert p.sleep_schedule is None
