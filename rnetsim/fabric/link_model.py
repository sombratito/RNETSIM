"""Link characteristic profiles for simulated media types.

Each profile defines the tc/netem parameters that simulate a physical medium.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkProfile:
    """Traffic shaping parameters for a simulated link."""

    medium: str
    bandwidth: str  # tc tbf rate (e.g., "5500", "50mbit")
    latency: str  # tc netem delay (e.g., "50ms")
    loss: str  # tc netem loss (e.g., "0%", "2%")
    jitter: str  # tc netem delay jitter (e.g., "50ms")


PROFILES: dict[str, LinkProfile] = {
    "lora_sf7_125": LinkProfile(
        medium="lora_sf7_125",
        bandwidth="5500",
        latency="50ms",
        loss="0%",
        jitter="50ms",
    ),
    "lora_sf8_125": LinkProfile(
        medium="lora_sf8_125",
        bandwidth="3100",
        latency="100ms",
        loss="0%",
        jitter="100ms",
    ),
    "lora_sf12_125": LinkProfile(
        medium="lora_sf12_125",
        bandwidth="293",
        latency="2000ms",
        loss="0%",
        jitter="2000ms",
    ),
    "wifi_local": LinkProfile(
        medium="wifi_local",
        bandwidth="50mbit",
        latency="2ms",
        loss="0%",
        jitter="1ms",
    ),
    "ethernet": LinkProfile(
        medium="ethernet",
        bandwidth="1gbit",
        latency="0.5ms",
        loss="0%",
        jitter="0.1ms",
    ),
    "internet": LinkProfile(
        medium="internet",
        bandwidth="50mbit",
        latency="50ms",
        loss="0.1%",
        jitter="20ms",
    ),
    "packet_radio": LinkProfile(
        medium="packet_radio",
        bandwidth="1200",
        latency="500ms",
        loss="2%",
        jitter="200ms",
    ),
    "satellite": LinkProfile(
        medium="satellite",
        bandwidth="64000",
        latency="800ms",
        loss="0.5%",
        jitter="100ms",
    ),
    "halow_4mhz": LinkProfile(
        medium="halow_4mhz",
        bandwidth="15mbit",
        latency="5ms",
        loss="0%",
        jitter="2ms",
    ),
    "sneakernet": LinkProfile(
        medium="sneakernet",
        bandwidth="100mbit",
        latency="1800000ms",
        loss="0%",
        jitter="300000ms",
    ),
}

VALID_MEDIUMS = set(PROFILES.keys())


def get_profile(medium: str) -> LinkProfile:
    """Get the link profile for a medium type.

    Raises ValueError if the medium is unknown.
    """
    if medium not in PROFILES:
        valid = ", ".join(sorted(VALID_MEDIUMS))
        raise ValueError(f"Unknown medium '{medium}'. Valid mediums: {valid}")
    return PROFILES[medium]
