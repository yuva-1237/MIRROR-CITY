import numpy as np
import networkx as nx
from typing import Dict, List, Any

class SpectralTrafficPropagator:
    """
    Spectral Graph Propagation Model for Urban Traffic Networks.
    
    This engine models traffic congestion diffusion across the street graph
    using an analytical spectral graph convolution operator based on the
    Kipf & Welling normalized graph Laplacian:
    
        H^(l+1) = ReLU( D_tilde^(-0.5) * A_tilde * D_tilde^(-0.5) * H^l * W^l )
        
    where:
      - A_tilde = A + I_N (street adjacency with self-loops, weighted by design speed)
      - D_tilde = Degree matrix of A_tilde
      - H^0 = Initial node feature vector derived from zoning type and population density
      - W^l = Spectral propagation decay parameters across 2 diffusion hops
      
    This model provides deterministic, high-throughput spatial propagation
    without relying on black-box external neural network weights.
    """
    def __init__(self, layers: int = 2):
        self.layers = layers

    def propagate_traffic(self, graph: nx.Graph) -> nx.Graph:
        """
        Run a 2-hop spectral graph propagation simulation to distribute congestion 
        across the city network topology.
        """
        nodes = list(graph.nodes())
        num_nodes = len(nodes)
        if num_nodes == 0:
            return graph
            
        node_indices = {node: i for i, node in enumerate(nodes)}

        # 1. Initialize Congestion Feature Vector H^0 (shape: [N, 1])
        H = np.zeros((num_nodes, 1))
        for node in nodes:
            idx = node_indices[node]
            # Use base population density and node type as initial congestion load
            pop = graph.nodes[node].get("population_density", 50.0)
            node_type = graph.nodes[node].get("type", "residential")
            
            # Industrial & Commercial zones start with higher traffic loads during peak hours
            type_weight = 1.4 if node_type in ["commercial", "industrial"] else 1.0
            H[idx, 0] = pop * type_weight / 100.0  # scale to [0, 1]

        # 2. Build Adjacency Matrix with Self-Loops (A_tilde = A + I)
        A = np.zeros((num_nodes, num_nodes))
        for u, v in graph.edges():
            if u in node_indices and v in node_indices:
                idx_u = node_indices[u]
                idx_v = node_indices[v]
                # Weight connection by speed limit (higher speed capacity = stronger propagation corridor)
                speed = graph.edges[u, v].get("speed_limit_kph", 50.0)
                link_weight = speed / 50.0
                A[idx_u, idx_v] = link_weight
                A[idx_v, idx_u] = link_weight

        A_tilde = A + np.eye(num_nodes)

        # 3. Calculate Normalized Adjacency D^-0.5 * A_tilde * D^-0.5
        degrees = np.sum(A_tilde, axis=1)
        # Avoid division by zero
        degrees = np.maximum(degrees, 1e-6)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(degrees))
        
        # Normalized Laplacian Adjacency
        A_norm = D_inv_sqrt @ A_tilde @ D_inv_sqrt

        # 4. Spectral Propagation Message-Passing Layers
        W_1 = 0.85  # hop 1 spectral propagation coefficient
        W_2 = 0.65  # hop 2 spectral propagation coefficient

        # Hop 1: first-order spectral neighborhood diffusion
        H_1 = A_norm @ H * W_1
        H_1 = np.maximum(0, H_1)

        # Hop 2: second-order spectral diffusion
        H_2 = A_norm @ H_1 * W_2
        H_output = np.maximum(0, H_2)

        # 5. Map output congestion back to graph nodes and edges
        for node in nodes:
            idx = node_indices[node]
            congestion = float(H_output[idx, 0])
            # Scale congestion index to [0.0, 1.0]
            graph.nodes[node]["congestion_index"] = round(min(1.0, congestion), 4)

        # Propagate node congestion to edges
        for u, v in graph.edges():
            cong_u = graph.nodes[u].get("congestion_index", 0.1)
            cong_v = graph.nodes[v].get("congestion_index", 0.1)
            edge_cong = (cong_u + cong_v) / 2.0
            
            # Incorporate direct edge level base congestion
            base_cong = graph.edges[u, v].get("base_congestion", 0.1)
            final_cong = min(1.0, base_cong + edge_cong * 0.5)
            
            graph.edges[u, v]["current_congestion"] = round(final_cong, 4)
            # Re-calculate travel time based on Bureau of Public Roads (BPR) function
            # Travel Time = Free Flow Time * (1 + 2.0 * (Congestion)^4)
            free_flow_time = (graph.edges[u, v]["length_m"] / 1000.0) / (graph.edges[u, v]["speed_limit_kph"] / 60.0)
            congested_time = free_flow_time * (1.0 + 2.0 * (final_cong ** 4))
            graph.edges[u, v]["travel_time_mins"] = round(congested_time, 2)

        return graph

# Backward-compatibility alias
TrafficGNN = SpectralTrafficPropagator
