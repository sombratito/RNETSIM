"""Tests for the radio propagation model — FSPL, link budget, viability."""

import math

import pytest

from rnetsim.fabric.radio_model import (
    DEFAULT_FREQUENCY_HZ,
    LORA_SENSITIVITY,
    OBSTRUCTION_PENALTY_DB,
    RadioResult,
    check_link_viability,
    fspl,
    medium_to_sf,
)


class TestFSPL:
    def test_zero_distance_returns_zero(self):
        assert fspl(0, 868_000_000) == 0.0

    def test_increases_with_distance(self):
        loss_1km = fspl(1000, 868_000_000)
        loss_10km = fspl(10000, 868_000_000)
        assert loss_10km > loss_1km

    def test_known_value_1km_868mhz(self):
        """FSPL at 1km, 868 MHz should be ~91.75 dB."""
        loss = fspl(1000, 868_000_000)
        assert loss == pytest.approx(91.25, abs=1.0)

    def test_doubles_distance_adds_6db(self):
        """Doubling distance should add ~6 dB (20*log10(2))."""
        loss_1 = fspl(1000, 868_000_000)
        loss_2 = fspl(2000, 868_000_000)
        assert (loss_2 - loss_1) == pytest.approx(6.02, abs=0.1)


class TestLinkViability:
    def test_short_range_viable(self):
        """100m LOS should always be viable."""
        result = check_link_viability(100, tx_power_dbm=20, spreading_factor="sf8")
        assert result.viable is True
        assert result.link_margin > 0

    def test_extreme_range_not_viable(self):
        """100km with obstructions should not be viable."""
        result = check_link_viability(
            100_000, tx_power_dbm=20, spreading_factor="sf8", is_los_clear=False
        )
        assert result.viable is False
        assert result.link_margin < 0

    def test_obstruction_reduces_margin(self):
        """Obstructed links should have less margin than clear ones."""
        clear = check_link_viability(5000, is_los_clear=True)
        blocked = check_link_viability(5000, is_los_clear=False)
        assert clear.link_margin > blocked.link_margin
        assert clear.link_margin - blocked.link_margin == pytest.approx(
            OBSTRUCTION_PENALTY_DB, abs=0.1
        )

    def test_higher_sf_longer_range(self):
        """SF12 should be viable at longer ranges than SF7."""
        distance = 15_000  # 15km
        sf7 = check_link_viability(distance, spreading_factor="sf7")
        sf12 = check_link_viability(distance, spreading_factor="sf12")
        assert sf12.link_margin > sf7.link_margin

    def test_result_fields_populated(self):
        result = check_link_viability(1000)
        assert isinstance(result, RadioResult)
        assert result.distance_m == pytest.approx(1000, abs=0.1)
        assert result.fspl_db > 0
        assert isinstance(result.rssi_estimate, float)
        assert isinstance(result.snr_estimate, float)


class TestMediumToSF:
    def test_known_mediums(self):
        assert medium_to_sf("lora_sf7_125") == "sf7"
        assert medium_to_sf("lora_sf8_125") == "sf8"
        assert medium_to_sf("lora_sf12_125") == "sf12"

    def test_unknown_defaults_to_sf8(self):
        assert medium_to_sf("wifi_local") == "sf8"
        assert medium_to_sf("unknown") == "sf8"
