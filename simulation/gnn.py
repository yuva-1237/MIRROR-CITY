"""
Legacy Compatibility Module for Traffic Simulation.

This module aliases TrafficGNN to SpectralTrafficPropagator.
The underlying model uses Kipf & Welling normalized graph Laplacian spectral propagation
(D^-0.5 * A_tilde * D^-0.5 * H * W) over city topology.
"""

from simulation.spectral_propagator import SpectralTrafficPropagator

# Maintain TrafficGNN as alias for backward compatibility
TrafficGNN = SpectralTrafficPropagator
__all__ = ["TrafficGNN", "SpectralTrafficPropagator"]

