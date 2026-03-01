# Reticulum Network Simulator

Docker-based simulation of heterogeneous Reticulum mesh networks
with real-time visualization, bandwidth shaping, and geographic modeling.

## Why This Exists

The Reticulum community has no network simulator. Developers building on Reticulum currently test by running multiple instances on localhost with TCP interfaces, or by setting up physical hardware. There is no way to simulate 50 LoRa nodes spread across a mountain range, or to model what happens when a Transport Instance goes offline, or to stress-test announce propagation at scale, or to visualize mesh topology changes in real time.

**rnetsim** fills this gap. It provides a Docker Compose environment where each simulated node is a real Reticulum instance running in its own container, connected to other nodes through a network fabric that simulates physical layer characteristics: bandwidth limits, latency, packet loss, geographic distance, and radio propagation. Community apps like Sideband, MeshChat, and NomadNet can connect to simulated nodes and function exactly as they would on real hardware.

This project is open source (MIT license) and contributed to the Reticulum community by Kingsland Academy LLC.
