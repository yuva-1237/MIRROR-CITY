import numpy as np
import networkx as nx
from typing import Dict, List, Any

class TrafficGNN:
    def __init__(self, layers: int = 2):
        self.layers = layers

    def propagate_traffic(self, graph: nx.Graph) -> nx.Graph:
        """
        Run a 2-layer Graph Convolution Network (GCN) simulation to propagate congestion 
        across the city network.
        Formula: H^(l+1) = D^-0.5 * A_tilde * D^-0.5 * H^l * W^l
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
            
            # Industrial & Commercial zones start with higher traffic loads during day
            type_weight = 1.4 if node_type in ["commercial", "industrial"] else 1.0
            H[idx, 0] = pop * type_weight / 100.0 # scale to [0, 1]

        # 2. Build Adjacency Matrix with Self-Loops (A_tilde = A + I)
        A = np.zeros((num_nodes, num_nodes))
        for u, v in graph.edges():
            if u in node_indices and v in node_indices:
                idx_u = node_indices[u]
                idx_v = node_indices[v]
                # Weight connection by speed limit (high speed = stronger propagation link)
                speed = graph.edges[u, v].get("speed_limit_kph", 50.0)
                link_weight = speed / 50.0
                A[idx_u, idx_v] = link_weight
                A[idx_v, idx_u] = link_weight

        A_tilde = A + np.eye(num_nodes)

        # 3. Calculate Degree Matrix D_tilde and normalize: D^-0.5 * A_tilde * D^-0.5
        degrees = np.sum(A_tilde, axis=1)
        D_inv_sqrt = np.diag(1.0 / np.sqrt(degrees))
        
        # Normalized Adjacency
        A_norm = D_inv_sqrt @ A_tilde @ D_inv_sqrt

        # 4. GCN Message Passing Layers (W_l represent simple propagation weights)
        W_1 = 0.85 # layer 1 propagation decay
        W_2 = 0.65 # layer 2 propagation decay

        # Layer 1
        H_1 = A_norm @ H * W_1
        # ReLu Activation (ensure non-negative)
        H_1 = np.maximum(0, H_1)

        # Layer 2
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
            
            # Incorporate any direct edge level congestion modifiers
            base_cong = graph.edges[u, v].get("base_congestion", 0.1)
            final_cong = min(1.0, base_cong + edge_cong * 0.5)
            
            graph.edges[u, v]["current_congestion"] = round(final_cong, 4)
            # Re-calculate travel time based on congestion (BPR function style)
            # Travel Time = Free Flow Time * (1 + 0.15 * (Congestion)^4)
            free_flow_time = (graph.edges[u, v]["length_m"] / 1000.0) / (graph.edges[u, v]["speed_limit_kph"] / 60.0) # in mins
            congested_time = free_flow_time * (1.0 + 2.0 * (final_cong ** 4))
            graph.edges[u, v]["travel_time_mins"] = round(congested_time, 2)

        return graph
