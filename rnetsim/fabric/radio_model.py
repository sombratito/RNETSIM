"""Radio propagation model for link viability calculations.

Implements free-space path loss (FSPL) and LoRa-specific link budget
calculations to determine if two nodes can communicate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RadioResult:
    """Result of a radio link viability check."""

    viable: bool
    rssi_estimate: float  # dBm
    snr_estimate: float  # dB
    link_margin: float  # dB (positive = viable)
    distance_m: float
    fspl_db: float


# LoRa receiver sensitivity per spreading factor (typical SX1262)
LORA_SENSITIVITY: dict[str, float] = {
    "sf7": -123.0,
    "sf8": -126.0,
    "sf9": -129.0,
    "sf10": -132.0,
    "sf11": -134.5,
    "sf12": -137.0,
}

# Default LoRa frequency (868 MHz EU / 915 MHz US)
DEFAULT_FREQUENCY_HZ = 868_000_000

# Default antenna gain
DEFAULT_ANTENNA_GAIN_DBI = 2.0

# Obstruction penalty when LOS is blocked
OBSTRUCTION_PENALTY_DB = 30.0


def fspl(distance_m: float, frequency_hz: float) -> float:
    """Calculate free-space path loss in dB.

    FSPL(dB) = 20*log10(d_m) + 20*log10(f_hz) - 147.55
    """
    if distance_m <= 0:
        return 0.0
    return 20 * math.log10(distance_m) + 20 * math.log10(frequency_hz) - 147.55


def check_link_viability(
    distance_m: float,
    tx_power_dbm: float = 20.0,
    antenna_gain_dbi: float = DEFAULT_ANTENNA_GAIN_DBI,
    spreading_factor: str = "sf8",
    frequency_hz: float = DEFAULT_FREQUENCY_HZ,
    is_los_clear: bool = True,
) -> RadioResult:
    """Check if a radio link is viable between two nodes.

    Uses FSPL + LoRa sensitivity to determine if signal is receivable.
    """
    path_loss = fspl(distance_m, frequency_hz)

    # Add obstruction penalty if LOS is blocked
    if not is_los_clear:
        path_loss += OBSTRUCTION_PENALTY_DB

    # Received signal strength
    rssi = tx_power_dbm + antenna_gain_dbi - path_loss

    # Get receiver sensitivity for this SF
    sensitivity = LORA_SENSITIVITY.get(spreading_factor, -126.0)

    # Link margin (positive = viable)
    margin = rssi - sensitivity

    # Rough SNR estimate (above noise floor)
    snr = rssi - (-120.0)  # typical noise floor

    return RadioResult(
        viable=margin > 0,
        rssi_estimate=round(rssi, 1),
        snr_estimate=round(snr, 1),
        link_margin=round(margin, 1),
        distance_m=round(distance_m, 1),
        fspl_db=round(path_loss, 1),
    )


def medium_to_sf(medium: str) -> str:
    """Extract spreading factor from medium name."""
    sf_map = {
        "lora_sf7_125": "sf7",
        "lora_sf8_125": "sf8",
        "lora_sf12_125": "sf12",
    }
    return sf_map.get(medium, "sf8")
