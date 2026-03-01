"""Device profile models and built-in profile definitions.

Each profile represents a hardware configuration with specific
radio, compute, and power characteristics.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DeviceProfile(BaseModel):
    """A device hardware profile for simulation nodes."""

    id: str
    name: str
    abbreviation: str
    color: str
    cpu: str
    ram: str
    radio: str
    bandwidth_display: str
    medium: str
    role: str = "endpoint"
    sleep_schedule: Optional[str] = None
    built_in: bool = True


BUILTIN_PROFILES: list[DeviceProfile] = [
    DeviceProfile(
        id="edge-c2",
        name="Edge C2",
        abbreviation="C2",
        color="#3b82f6",
        cpu="4x A76",
        ram="4 GB",
        radio="LoRa SF8",
        bandwidth_display="3.1 kbps",
        medium="lora_sf8_125",
        role="transport",
    ),
    DeviceProfile(
        id="field-node",
        name="Field Node",
        abbreviation="FN",
        color="#22c55e",
        cpu="4x A53",
        ram="512 MB",
        radio="LoRa SF8",
        bandwidth_display="3.1 kbps",
        medium="lora_sf8_125",
        role="endpoint",
        sleep_schedule="5/55",
    ),
    DeviceProfile(
        id="halow-bridge",
        name="HaLow Bridge",
        abbreviation="HW",
        color="#a855f7",
        cpu="4x A76",
        ram="4 GB",
        radio="HaLow 4 MHz",
        bandwidth_display="15 Mbps",
        medium="halow_4mhz",
        role="transport",
    ),
    DeviceProfile(
        id="solar-sensor",
        name="Solar Sensor",
        abbreviation="SS",
        color="#eab308",
        cpu="1x LX7",
        ram="520 KB",
        radio="LoRa SF12",
        bandwidth_display="293 bps",
        medium="lora_sf12_125",
        role="endpoint",
        sleep_schedule="1/59",
    ),
    DeviceProfile(
        id="hilltop-relay",
        name="Hilltop Relay",
        abbreviation="HR",
        color="#ef4444",
        cpu="2x A72",
        ram="4 GB",
        radio="LoRa SF7",
        bandwidth_display="5.5 kbps",
        medium="lora_sf7_125",
        role="transport",
    ),
    DeviceProfile(
        id="roaming-relay",
        name="Roaming Relay",
        abbreviation="RR",
        color="#06b6d4",
        cpu="4x A53",
        ram="512 MB",
        radio="LoRa SF8",
        bandwidth_display="3.1 kbps",
        medium="lora_sf8_125",
        role="transport",
    ),
    DeviceProfile(
        id="packet-radio-tnc",
        name="Packet Radio TNC",
        abbreviation="PR",
        color="#f97316",
        cpu="1x A53",
        ram="256 MB",
        radio="1200 baud",
        bandwidth_display="1.2 kbps",
        medium="packet_radio",
        role="transport",
    ),
    DeviceProfile(
        id="internet-backhaul",
        name="Internet Backhaul",
        abbreviation="IB",
        color="#6b7280",
        cpu="4x A76",
        ram="4 GB",
        radio="TCP/IP",
        bandwidth_display="100 Mbps",
        medium="internet",
        role="transport",
    ),
    DeviceProfile(
        id="sneakernet-courier",
        name="Sneakernet Courier",
        abbreviation="SN",
        color="#d97706",
        cpu="1x A53",
        ram="256 MB",
        radio="USB 3.0",
        bandwidth_display="100 Mbps",
        medium="sneakernet",
        role="transport",
    ),
]

BUILTIN_PROFILE_MAP: dict[str, DeviceProfile] = {p.id: p for p in BUILTIN_PROFILES}
