"""Tests for gateway bridge functionality."""

from rnetsim.gateway.bridge import generate_client_config, get_gateway_port_mapping


class TestGatewayPortMapping:
    def test_returns_correct_docker_format(self):
        mapping = get_gateway_port_mapping(14242)
        assert mapping == {"4242/tcp": 14242}

    def test_default_reticulum_port(self):
        mapping = get_gateway_port_mapping(5000)
        assert "4242/tcp" in mapping
        assert mapping["4242/tcp"] == 5000


class TestGenerateClientConfig:
    def test_contains_interface_type(self):
        config = generate_client_config(14242)
        assert "TCPClientInterface" in config

    def test_contains_port(self):
        config = generate_client_config(14242)
        assert "14242" in config

    def test_targets_localhost(self):
        config = generate_client_config(14242)
        assert "localhost" in config

    def test_custom_interface_name(self):
        config = generate_client_config(14242, interface_name="My Gateway")
        assert "My Gateway" in config

    def test_ini_format(self):
        """Config should be valid Reticulum INI format with double brackets."""
        config = generate_client_config(14242)
        assert config.startswith("[[")
        assert "type = TCPClientInterface" in config
        assert "target_host = localhost" in config
        assert "target_port = 14242" in config
