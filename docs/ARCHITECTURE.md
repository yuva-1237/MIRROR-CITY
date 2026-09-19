# 🏛️ MIRROR-CITY Mathematical & Architectural Specification

This document provides an in-depth mathematical specification of the simulation dynamics, state propagation, multi-agent arbitration mechanics, and time-series telemetry forecasters powering the **MIRROR-CITY** urban digital twin.

---

## Table of Contents
1. [Simulation Mathematics](#1-simulation-mathematics)
   - [1.1 Traffic Network & Spectral Graph Diffusion](#11-traffic-network--spectral-graph-diffusion)
   - [1.2 Travel Time Modeling: Bureau of Public Roads (BPR) Function](#12-travel-time-modeling-bureau-of-public-roads-bpr-function)
   - [1.3 Hydraulic Runoff & Inundation Propagation](#13-hydraulic-runoff--inundation-propagation)
   - [1.4 Pedestrian Micro-Dynamics & Social Force Potential](#14-pedestrian-micro-dynamics--social-force-potential)
   - [1.5 Diurnal Peak Forecaster (Fourier Basis Representation)](#15-diurnal-peak-forecaster-fourier-basis-representation)
2. [Multi-Agent Conflict Arbitration](#2-multi-agent-conflict-arbitration)
   - [2.1 Peer Schema Contract](#21-peer-schema-contract)
   - [2.2 Cross-Domain Incompatibility Detection](#22-cross-domain-incompatibility-detection)
   - [2.3 Multi-Objective Pareto Optimization & Compromise Scoring](#23-multi-objective-pareto-optimization--compromise-scoring)
3. [Telemetry Attribution & Explainability (XAI)](#3-telemetry-attribution--explainability-xai)
   - [3.1 Threshold-Attribution Ingestion](#31-threshold-attribution-ingestion)
   - [3.2 Sensitivity & Impact Scaling](#32-sensitivity--impact-scaling)
4. [Storage Engine & State Lifecycle](#4-storage-engine--state-lifecycle)

---

## 1. Simulation Mathematics

### 1.1 Traffic Network & Spectral Graph Diffusion

The city's transit grid is formalized as a directed, edge-weighted graph:

$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathbf{W})$$

where:
- $\mathcal{V} = \{v_1, v_2, \dots, v_N\}$ is the set of $N$ road intersections / junctions.
- $\mathcal{E} \subseteq \mathcal{V} \times \mathcal{V}$ is the set of $M$ directed arterial street segments.
- $\mathbf{W} \in \mathbb{R}^{N \times N}$ is the adjacency weight matrix, where $W_{ij} = \frac{1}{\text{distance}(v_i, v_j)}$ if $(v_i, v_j) \in \mathcal{E}$, else $0$.

Let $\mathbf{D} \in \mathbb{R}^{N \times N}$ be the diagonal degree matrix:

$$D_{ii} = \sum_{j=1}^N W_{ij}$$

The **Normalized Symmetric Graph Laplacian** $\mathbf{L}_{sym}$ governs spatial heat and congestion propagation:

$$\mathbf{L}_{sym} = \mathbf{I}_N - \mathbf{D}^{-1/2} \mathbf{W} \mathbf{D}^{-1/2}$$

Let $\mathbf{c}(t) \in [0, 1]^N$ be the instantaneous node congestion state vector at time $t$. The continuous-time spatial diffusion of localized traffic bottlenecks follows the parabolic heat dissipation differential equation:

$$\frac{\partial \mathbf{c}(t)}{\partial t} = -\kappa \, \mathbf{L}_{sym} \, \mathbf{c}(t) + \mathbf{s}(t) - \gamma \, \mathbf{c}(t)$$

where:
- $\kappa > 0$ is the **spatial spillover conductivity** (governed by road connectivity).
- $\mathbf{s}(t) \in \mathbb{R}^N$ represents external traffic injection (spikes from events, stadium ingress, or accidents).
- $\gamma > 0$ is the natural **drainage coefficient** representing clear-flow discharge capacity.

In discrete time with step size $\Delta t$:

$$\mathbf{c}^{(t + 1)} = \mathbf{c}^{(t)} + \Delta t \left( -\kappa \mathbf{L}_{sym} \mathbf{c}^{(t)} + \mathbf{s}^{(t)} - \gamma \mathbf{c}^{(t)} \right)$$

---

### 1.2 Travel Time Modeling: Bureau of Public Roads (BPR) Function

To compute real-time trip delay along any directed link $e = (v_i, v_j)$, the engine evaluates the standard **Federal Highway Administration BPR formulation**:

$$T_e(V_e) = T_{e,0} \cdot \left[ 1 + \alpha \left( \frac{V_e}{C_e} \right)^\beta \right]$$

where:
- $T_{e,0} = \frac{\text{length}(e)}{\text{speed\_limit}(e)}$ is the free-flow traversal time.
- $V_e$ is the instantaneous vehicular volume (vehicles/hour).
- $C_e$ is the practical road capacity before level-of-service breakdown.
- $\alpha = 0.15$ and $\beta = 4.0$ are empirical calibration exponents.

When $V_e > C_e$ ($V/C > 1.0$), travel time scales exponentially with exponent 4, precipitating gridlock alerts in the Traffic Agent.

---

### 1.3 Hydraulic Runoff & Inundation Propagation

Urban stormwater accumulation is evaluated using a 2D kinematic wave approximation combined with the **Rational Runoff Equation**:

$$Q = C \cdot I \cdot A$$

where:
- $Q$ is peak surface runoff rate ($\text{m}^3/\text{s}$).
- $C \in [0.1, 0.95]$ is the dimensionless runoff coefficient based on land cover ($C_{\text{asphalt}} = 0.90$, $C_{\text{park}} = 0.20$).
- $I$ is precipitation rainfall intensity ($\text{mm}/\text{hr}$).
- $A$ is catchment drainage area ($\text{m}^2$).

Overland sheet flow velocity $v$ across street gutters follows **Manning's Formula**:

$$v = \frac{1}{n} R_h^{2/3} S_0^{1/2}$$

where:
- $n$ is Manning's roughness coefficient ($n = 0.013$ for paved concrete streets).
- $R_h = \frac{A_w}{P_w}$ is the hydraulic radius (cross-sectional flow area divided by wetted perimeter).
- $S_0 = \frac{\Delta h}{L}$ is the street bed slope (elevation gradient).

Water height $h_i(t)$ at intersection node $i$ increments when inflow exceeds storm drain throughput capacity $\Omega_{drain}$:

$$\frac{d h_i}{dt} = \frac{Q_{in, i} - \Omega_{drain, i}}{A_{surface, i}}$$

If $h_i > 0.15\,\text{m}$ (6 inches), passenger vehicles stall; if $h_i > 0.30\,\text{m}$, emergency response routing redirects away from the sector.

---

### 1.4 Pedestrian Micro-Dynamics & Social Force Potential

Pedestrian density surges around high-density transit hubs (e.g., Embarcadero, Powell St Station) are simulated using **Helbing's Social Force Model**:

$$m_p \frac{d\mathbf{v}_p}{dt} = \mathbf{f}_p^0 + \sum_{q \ne p} \mathbf{f}_{pq}^{soc} + \sum_{b \in \mathcal{B}} \mathbf{f}_{pb}^{obs}$$

1. **Desired Destination Acceleration**:
   $$\mathbf{f}_p^0 = m_p \frac{v_p^0 \mathbf{e}_p^0 - \mathbf{v}_p}{\tau}$$
   where $v_p^0$ is desired walking speed ($\approx 1.34\,\text{m/s}$), $\mathbf{e}_p^0$ is the destination unit vector, and $\tau \approx 0.5\,\text{s}$ is the relaxation time.

2. **Inter-Pedestrian Repulsive Force**:
   $$\mathbf{f}_{pq}^{soc} = A_i \exp\left(\frac{r_{pq} - d_{pq}}{B_i}\right) \mathbf{n}_{pq}$$
   where $r_{pq} = r_p + r_q$ is the sum of personal radii, $d_{pq}$ is Euclidean distance, and $A_i, B_i$ modulate psychological boundary thresholds.

3. **Obstacle/Building Repulsion**:
   $$\mathbf{f}_{pb}^{obs} = A_b \exp\left(\frac{r_p - d_{pb}}{B_b}\right) \mathbf{n}_{pb}$$

Crowd crush or panic alerts trigger if spatial density $\rho = \frac{N_{\text{agents}}}{Area} > 4.0\,\text{persons/m}^2$.

---

### 1.5 Diurnal Peak Forecaster (Fourier Basis Representation)

To forecast realistic 24-hour congestion curves, the system fits historical hourly telemetry to a two-harmonic trigonometric series representing morning and evening rush hours:

$$C_{pred}(t) = \mu + A_1 \cos\left(\frac{2\pi (t - \phi_1)}{24}\right) + A_2 \cos\left(\frac{4\pi (t - \phi_2)}{24}\right) + \epsilon(t)$$

- Peak 1 (Morning Commute): $\phi_1 \approx 8.5$ hours (8:30 AM).
- Peak 2 (Evening Rush): $\phi_2 \approx 17.5$ hours (5:30 PM).
- $\epsilon(t) \sim \mathcal{N}(0, \sigma^2)$ injects stochastic variations calibrated to weather conditions.

---

## 2. Multi-Agent Conflict Arbitration

MIRROR-CITY deploys 10 specialized domain agents operating concurrently:
`Traffic`, `Disaster`, `Energy`, `Health`, `Environment`, `Economy`, `Transit`, `Water`, `Housing`, `Police`.

```
                  ┌───────────────────────────────┐
                  │ 10 Domain Autonomous Agents  │
                  └──────────────┬────────────────┘
                                 │ Structured Peer Schema
                                 ▼
                  ┌───────────────────────────────┐
                  │  Conflict Resolver Engine     │
                  │  (agents/conflict_resolver.py)│
                  └──────────────┬────────────────┘
                                 │
            ┌────────────────────┴────────────────────┐
            ▼                                         ▼
   Incompatibility Rules                      Consensus Metric
(Zone Flood vs Construction,               $C = 1 - \frac{1}{2M}\sum |s_i - s_j|$
 Economic Gain vs GHG Cap)                            │
            │                                         ▼
            └────────────────────┬────────────────────┘
                                 ▼
                  ┌───────────────────────────────┐
                  │   Pareto Compromise Report    │
                  │ - Dominant Trade-offs         │
                  │ - Mitigated Joint Policy      │
                  │ - Projected Resiliency Impact │
                  └───────────────────────────────┘
```

### 2.1 Peer Schema Contract

Every agent outputs a deterministic, strongly-typed JSON structure:

```json
{
  "agent_id": "economy",
  "status": "optimal",
  "proposals": [
    {
      "id": "prop-econ-01",
      "action": "arterial_widening_grant",
      "target_zone": "SOMA",
      "priority": "high",
      "cost_estimate_usd": 12500000
    }
  ],
  "concerns": [
    {
      "issue": "Commercial logistics delay exceeding 22 minutes on Highway 101",
      "severity": 0.72
    }
  ],
  "telemetry_drivers": [
    {
      "metric": "commercial_throughput",
      "observed_value": 4120.0,
      "baseline_value": 6000.0,
      "threshold": 4800.0,
      "unit": "vehicles/hr",
      "impact": "critical"
    }
  ]
}
```

### 2.2 Cross-Domain Incompatibility Detection

Conflicts emerge when two agents propose diametrically opposed actions for the same spatial coordinate or resource pool:

| Agent A Proposal | Agent B Objection / Conflict | Detected Incompatibility Rule |
| :--- | :--- | :--- |
| **Economy**: Road Widening / Arterial Expansion | **Disaster**: 100-Year Flood Zone Inundation Risk | `CIVIL_WORKS_IN_ACTIVE_FLOOD_BASIN` |
| **Economy**: Commercial Port Rezoning | **Environment**: $\text{NO}_x / \text{PM}_{2.5}$ Microclimate Cap | `EMISSION_CEILING_EXCEEDED` |
| **Traffic**: Signal Phase Green Extension | **Transit**: Bus Rapid Transit (BRT) Headway Penalty | `TRANSIT_PRIORITY_INVERSION` |
| **Housing**: High-Density Rezoning | **Water**: Aquifer Pressure & Fire Hydrant Flow Limit | `HYDRAULIC_INFRASTRUCTURE_DEFICIT` |

### 2.3 Multi-Objective Pareto Optimization & Compromise Scoring

Let $\mathcal{A} = \{a_1, a_2, \dots, a_K\}$ be the candidate interventions. Each agent $j$ evaluates candidate $a_k$ with utility score $u_{j}(a_k) \in [-1, +1]$.

The overall Consensus Score $C$ across $M$ conflicting agents is defined as:

$$C(\mathcal{A}) = 1.0 - \frac{1}{2 M (M - 1)} \sum_{i=1}^M \sum_{j \ne i}^M \left| u_i(a) - u_j(a) \right|$$

- $C = 1.0$: Total mutual consensus.
- $C \to 0.0$: Maximum polarization and adversarial gridlock.

The **Conflict Resolver** generates an arbitrated compromise policy by selecting solutions on the Pareto frontier that maximize joint urban resilience:

$$\max_{a} \quad \sum_{j=1}^M w_j u_j(a) \quad \text{subject to} \quad \min_{j} u_j(a) \ge -\theta_{\text{veto}}$$

where $w_j$ are statutory policy weights (e.g., Public Safety / Life Preservation receives strict priority over Short-term Economic ROI during emergencies).

---

## 3. Telemetry Attribution & Explainability (XAI)

MIRROR-CITY ensures zero "black-box" decision making. Planners and evaluators inspect why any recommendation was made down to the exact telemetry sensor reading.

### 3.1 Threshold-Attribution Ingestion

For every alert or proposal, the agent computes an attribution tuple:

$$\langle \mu_{\text{observed}}, \mu_{\text{baseline}}, \tau_{\text{critical}}, \delta_{\text{normalized}} \rangle$$

$$\delta_{\text{normalized}} = \frac{|\mu_{\text{observed}} - \tau_{\text{critical}}|}{\sigma_{\text{historical}}}$$

### 3.2 Sensitivity & Impact Scaling

An explanation card is surfaced in the UI if $\delta_{\text{normalized}} > 1.0$:
- **Impact = "critical"**: $\mu_{\text{observed}}$ exceeds safety threshold by $> 25\%$.
- **Impact = "warning"**: $\mu_{\text{observed}}$ within $10\%\text{--}25\%$ of regulatory envelope.
- **Impact = "info"**: Sub-threshold seasonal fluctuation.

Example explainability attribution quote:
> *"Traffic Agent flagged Corridor Market St because congestion = 88.4%, which exceeds the critical threshold of 80.0% (baseline: 42.0%)."*

---

## 4. Storage Engine & State Lifecycle

```
[ Telemetry Ingestion ] ──> [ Rolling State Buffer (RAM) ]
                                    │
                                    ├───> SQLite Persistent Ledger (wal mode)
                                    │     ├── scenarios table (snapshots & forks)
                                    │     ├── agent_logs table (attribution audit)
                                    │     └── metrics_history table (time-series)
                                    │
                                    └───> FastAPI WebSocket Broadcaster
                                          └───> React / Deck.gl 3D Client
```

- **Persistence Layer**: Embedded SQLite with Write-Ahead Logging (`PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;`).
- **Telemetry Throughput**: Real-time evaluation loop operating at 1.0 Hz with sub-50ms tick latency.
- **Scenario Forking**: Deep copy-on-write snapshotting of all graph node weights, asset attributes, and agent memory vectors.
