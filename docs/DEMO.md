# ⏱️ MIRROR-CITY 5-Minute Technical Demo Script

**Target Audience**: Senior Engineers, Technical Interviewers, Urban Planning Evaluators, and Judges.  
**Demonstration Time**: Exactly 5 minutes (300 seconds).  
**Core Thesis**: *"Urban digital twins shouldn't just be passive dashboards. MIRROR-CITY is an autonomous multi-agent operating system that models real-world physics, arbitrates conflicting civic priorities, and provides full explainability down to the telemetry sensor."*

---

## 🕒 Minute-by-Minute Timeline Overview

| Minute | Segment | Focus Area | Key UI Action |
| :---: | :--- | :--- | :--- |
| **0:00 - 1:00** | **The Hook & Problem** | Why traditional smart cities fail | Overview Dashboard & Live Ticker |
| **1:00 - 2:00** | **The 3D Digital Twin** | High-fidelity geospatial physics | Switch to Deck.gl 3D SF Financial District |
| **2:00 - 3:00** | **Multi-Agent Collaboration** | Cross-domain conflict arbitration | Open "Agent Collaboration & Trade-offs" |
| **3:00 - 4:00** | **Scenario A/B Planner** | Before-and-after policy evaluation | Open "Scenario Compare", toggle diffs & CSV export |
| **4:00 - 5:00** | **Explainability & Wrap-up** | Zero black-box telemetry attribution | Open "Explainability Panel" + Honest Limitations |

---

## 🎬 Minute 0:00 – 1:00 | The Hook & The Problem

### 🗣️ Speaker Script:
> *"Good morning. Today, modern cities operate in deep silos. When public works widens a highway, economic activity expands—but disaster response models show runoff risk escalates, and housing density plunges.*
> 
> *Most 'smart city' platforms are nothing more than read-only KPI dashboards. **MIRROR-CITY** is different: it is an agentic, cyber-physical operating system where 10 autonomous domain agents collaborate, simulate consequences, and negotiate trade-offs in real time.*
> 
> *Here on the main Operations Center, you can see live telemetry streaming across energy grids, traffic densities, emergency response dispatch, and water tables. Every single metric is connected to an underlying graph simulation."*

### 🖱️ Actions:
1. Open web browser to `http://localhost:5173`.
2. Point cursor to the top ticker showing live city health score, carbon index, and active alerts.
3. Show the real-time simulation tick updating without page reload via WebSocket.

---

## 🏙️ Minute 1:00 – 2:00 | The 3D Digital Twin (San Francisco)

### 🗣️ Speaker Script:
> *"Let's zoom into our 3D spatial twin. Rather than an abstract 2D map, we render volumetric building structures and spatial telemetry using Deck.gl and WebGL.*
> 
> *Here in the San Francisco Financial District, we have high-precision building footprints: Salesforce Tower, Transamerica Pyramid, 555 California, and the Embarcadero Center.*
> 
> *Watch how the 3D congestion cylinders rise above arterial intersections. Red columns signify BPR level-of-service breakdown—congestion exceeding 85%—while green corridors indicate fluid throughput. Notice the animated flow arcs visualizing commuter migration from SoMa into the financial core."*

### 🖱️ Actions:
1. Click on the **"3D View"** tab in the navigation bar.
2. Click the **"Salesforce Tower"** camera preset to orbit the skyscraper cluster.
3. Click on a red congestion cylinder (e.g., *Market & 4th St*) to show the elevation tooltip and volume/capacity ratio.
4. Rotate the camera using right-click drag to demonstrate 60fps smooth WebGL performance.

---

## 🤝 Minute 2:00 – 3:00 | Multi-Agent Collaboration & Conflict Arbitration

### 🗣️ Speaker Script:
> *"Here is the crown jewel of MIRROR-CITY: multi-agent collaborative arbitration.*
> 
> *In traditional AI demos, agents operate in vacuum bubbles. In our system, each agent outputs a structured peer schema containing proposals, objections, and telemetry drivers.*
> 
> *Look at this detected conflict: The **Economy Agent** proposes widening a 4-lane arterial in the lower basin to unlock $12.5M in logistics throughput. But immediately, our **Disaster Agent** raises a critical veto: that specific corridor lies directly in a 100-year storm surge flood plain.*
> 
> *Instead of crashing or hallucinating, our **Conflict Resolver Engine** executes a Pareto compromise calculation. It generates this arbitrated trade-off report: approve high-permeability permeable pavement and elevated retention basins, capturing 78% of the economic gains while preserving 100% of flood mitigation safety."*

### 🖱️ Actions:
1. Click on the **"Agent Collaboration"** tab.
2. Show the **Conflict Matrix** card displaying the red badge: `CIVIL_WORKS_IN_ACTIVE_FLOOD_BASIN`.
3. Point out the **Consensus Score gauge** (e.g., `0.74 / 1.00`).
4. Expand the **"Arbitrated Trade-off Report"** card, showing the joint policy and mitigated risk projection.

---

## 📊 Minute 3:00 – 4:00 | Scenario A/B Planner Comparison

### 🗣️ Speaker Script:
> *"City planners cannot afford to guess. They need concrete before-and-after proof before breaking ground.*
> 
> *In our **Scenario Compare** module, we place the **Baseline City State** side-by-side with an experimental intervention—for instance, 'Peak Storm Inundation with Congestion Pricing'.*
> 
> *Instantly, our differential engine computes deltas across all primary KPIs: Congestion drops by -14.2%, Average Speed improves by +7.4 km/h, Carbon Footprint decreases by -11.8%, while Emergency Response delay increases slightly by +0.8 minutes due to rerouting.*
> 
> *Planners can inspect the exact asset modifications in the diff table—such as sub-station closures or signal retiming—and export the audit trail directly to CSV for city council review."*

### 🖱️ Actions:
1. Click on the **"Scenario Compare"** tab.
2. Highlight the 4 delta cards (Green badge `-14.2%` Congestion, etc.).
3. Scroll to the **"Asset State & Infrastructure Diffs"** table showing modified roads and power substations.
4. Click the **"Export CSV"** button and highlight the generated download toast.

---

## 🔍 Minute 4:00 – 5:00 | Explainable AI (XAI) & Honest Limitations

### 🗣️ Speaker Script:
> *"Finally, we address the biggest problem in modern AI: transparency. Our README tag promises 'Explainable AI'—and here it is in production.*
> 
> *Opening our **Explainability Panel**, every agent recommendation is tied to the exact sensor telemetry that triggered it. For instance: 'Traffic Agent flagged corridor Market St because observed congestion was 88.4%, breaching the critical threshold of 80.0% against a historical baseline of 42.0%'. There is zero hallucination.*
> 
> *To be fully transparent as engineers, we also document our current boundaries in the README:*
> 1. *Our congestion baselines currently use synthetic diurnal Fourier curves rather than live city sensor feeds;*
> 2. *We use an embedded SQLite database with Write-Ahead Logging optimized for single-city twins rather than distributed CockroachDB;*
> 3. *And our spatial graph diffusion relies on fixed-weight graph Laplacians rather than dynamic end-to-end trained GCN weights.*
> 
> *Thank you—I am now happy to open up for any technical questions regarding our graph algorithms or multi-agent arbitration engine."*

### 🖱️ Actions:
1. Click on the **"Explainability"** tab.
2. Point out the telemetry driver cards with visual progress bars comparing *Observed* vs *Threshold* vs *Baseline*.
3. Show the exact quote card: *"Traffic Agent flagged corridor..."*.
4. Conclude on the dashboard and welcome questions.

---

## ❓ Evaluator & Interviewer FAQ Prep

### Q1: *"How does the Conflict Resolver prevent deadlocks if two agents have equal priority?"*
> **Answer**: *"We implement a hierarchical constraint satisfaction model. Public safety (Disaster, Health, Police) holds an absolute safety veto $\theta_{veto} = 0.85$. If life safety isn't compromised, the resolver evaluates Pareto utility $\sum w_j u_j(a)$, where weights $w_j$ can be re-weighted by city council policy presets."*

### Q2: *"Why Deck.gl instead of Cesium or Three.js?"*
> **Answer**: *"Deck.gl is purpose-built for large-scale geospatial visualization. It handles millions of data points on the GPU via WebGL instancing. Our building extrusion layers and animated transit arcs render at a steady 60 FPS without overloading the JavaScript main thread."*

### Q3: *"Can this scale to a real city like New York or Tokyo?"*
> **Answer**: *"The spatial graph diffusion equation ($\mathbf{L}_{sym}$) scales to tens of thousands of intersections using sparse matrix solvers ($O(N + M)$ complexity). For distributed multi-city clusters, the next architectural step is replacing SQLite with TimescaleDB or PostgreSQL with PostGIS."*
