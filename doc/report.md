# TSP with Sequence Constraints and Non-Linear Objective

## 1. Summary

This document outlines a solution approach to the "problem" (see README.md). First, we establish lower and upper bounds to frame solution quality, then generate feasible routes via construction heuristics. Next, iterative improvements leverage neighbourhood operators used by local search, simulated annealing (SA), and adaptive large neighbourhood search (ALNS). SA and ALNS can escape local optima. ALNS is implemented with the `alns` package ([link](https://pypi.org/project/alns/)). A monitoring and reporting layer tracks progress.

Numerical results are presented. Notably, within 10 seconds all implementations can provide a feasible solution. Surprisingly, greedy local search often yields the best solution identified.

Finally, future work suggestions are listed.

## 2. Architecture & Design

### 2.1 High-Level Diagram

The following diagram captures how the main optimisation stages interact with shared data stores and supporting services.

![High Level Diagram](/doc/hld.drawio.png "HLD")

**Key data models:** `Node`, `Route`

### 2.2 Component Organization

This catalog summarises the major subsystems, their responsibilities, and the classes that realise each capability.

| Component | Purpose | Key Classes |
|-----------|---------|-------------|
| `Data Layer` | Data ingestion, validation, storage | `CSVParser`, `NodeValidator`, `NodeManager`, `EdgeManager`, `DistanceManager` |
| `Bound Estimation` | Solution bounds | `LowerBoundCalculator`, `UpperBoundCalculator` |
| `Construction Heuristics` | Create initial route | `NaiveSequencer` |
| `Evaluation` | Route evaluation and validation | `RouteEvaluator` |
| `Neighbourhood Operators` | Local search operators | `TwoOptSwap`, `ThreeOptSwap`, `Relocate` |
| `Termination` | Stopping criteria | `Termination` |
| `Iterative Metaheuristics` | Improvement metaheuristics | `LocalSearchImprover`, `SimulatedAnnealingImprover`, `ALNSWrapper` |
| `Monitoring & Reporting` | Visualisation and export | `Callback`, `RouteExporter`, `RoutePlotBuilder` |

### 2.3 Data Flow

The numbered steps below outline the runtime pipeline from raw inputs to exported results, showing how intermediate products feed subsequent heuristics and reporting.

1. Parse and validate input
2. Construct data managers
3. Estimate lower and upper bounds
4. Construct initial feasible solution
5. Iteratively improve the solution (via local search, simulated annealing, or adaptive large neighbourhood search)
6. Export results and generate plots

---

## 3. Methodology

This section outlines the sequential techniques used to build, assess, and refine candidate routes, moving from bounding analyses to constructive and metaheuristic refinements.

### 3.1 Lower and Upper Bound Estimation

**Lower bound:** identify both the minimum and maximum pairwise distances to compute $\text{LB} = \min(d_{ij}) \cdot n \cdot (\max(d_{ij}) + 1)$, where $d_ij$ is the distance from $i$ to $j$.

**Upper bound formula:** identify the maximum distance to derive $\text{UB} = \max(d_{ij}) \cdot n \cdot (\max(d_{ij}) + 1)$, providing a ceiling on achievable objective values, where $d_ij$ is the distance from $i$ to $j$.

### 3.2 Construction Heuristics

The construction phase quickly produces feasible starting tours whose structure can be refined by later improvement phases.

#### Naive Sequencer

The naïve sequencer visits even-indexed nodes (sorted) before the odd ones, producing a feasible baseline tour that respects the problem's ordering constraints. This straightforward pass provides a quick starting point.

Pseudocode:

```text
INPUT  nodes
OUTPUT sequence

origin ← nodes[0]
destination ← nodes[-1]
intermediates ← nodes[1:-1]

even_nodes ← {node | (index % 2 = 0) for (index, node) in enumerate(intermediates)}
odd_nodes ← {node | (index % 2 = 1) for (index, node) in enumerate(intermediates)}
RETURN origin + sort_decreasing(even_nodes) + sort_increasing(odd_nodes) + destination
```

### 3.3 Metaheuristics

After constructing an initial tour, iterative metaheuristics explore the solution neighbourhood to identify improvements.

#### 3.3.1 Local Search

The local search walks the neighbourhood using a first-improvement policy.

**Acceptance criterion:** as soon as it lowers the objective

**Termination:** the process repeats until a time, iteration, or lower-bound termination condition is met.

**Operators used:** it applies 2-Opt, 3-Opt, or Relocate moves in sequence and over multiple cycles

| Operator | Mechanism |
|----------|-----------|
| **2-Opt Swap** | Reverses a segment to reduce crossings |
| **3-Opt Swap** | Removes three edges, explores eight reconnections |
| **Relocate** | Moves a segment to a new position |

#### 3.3.2 Simulated Annealing (SA)

Simulated annealing escapes local optima through probabilistic acceptance guided by a geometric cooling schedule ( $T_{t+1} = T_{t} \cdot \text{cooling\_rate}$ ).

**Acceptance criterion:** Metropolis rule ($e^{-\Delta/T}$) determines whether to accept worse moves (improvements are always accepted)

**Termination:** the algorithm iterates until a time, iteration, or lower-bound threshold is met.

**Parameters:** initial temperature, cooling rate, minimum temperature.

**Operators used:** randomly select 2-Opt, 3-Opt, or Relocate while maintaining feasibility

#### 3.3.3 Adaptive Large Neighbourhood Search (ALNS)

ALNS is implemented using the package: [alns](https://pypi.org/project/alns/)

ALNS combines late-acceptance hill climbing with a portfolio of destroy and repair operators to mutate feasible tours. A roulette-wheel scheme with adaptive weights selects operators proportionally to their historical performance.

**Acceptance criterion:** late acceptance hill climbing

**Termination:** the run concludes when iteration, time, or bound limits trigger termination

**Operators used:**
* **Destroy operators:** random removal, path removal, worst removal
* **Repair operator:** greedy repair to maintain feasibility
* **Selection strategy:** roulette wheel with adaptive weights

## 4. Other Features

Beyond pure optimisation logic, the solution bundles supporting capabilities for insight and reuse.

### 4.1 Monitoring via Callback System

Monitoring callbacks capture iteration-by-iteration progress.

- **Tracking:** iteration number, current value, best value, improvement flag
- **Route saving:** store routes at specific iterations, for example when improvement is achieved

### 4.2 Data Structures

Structured node and route keep downstream tooling consistent. While cached distance supports efficiency.

- **Nodes:** Pydantic model with support for hashing.
- **Route objects:** Pydantic model with sequence of nodes.
- **Distance matrix:** symmetric caching for efficiency.

---

## 5. Experimental Results

Available datasets have 20, 30, 40, 50, and 60 nodes. Deterministic seeding was used for reproducibility. Termination was set to 10 seconds or 10,000 iterations.

### 5.1 Assumptions

- Node IDs are non-negative integers.
- A feasible solution always exists.
- Distances are symmetric ($d_{ij} = d_{ji}$), but the distance from the last depot to the first depot is zero (this enables to create a canonical TSP loop)

### 5.3 Numerical Results

All solutions in this comparison are initialized from the same random.

The best found route per dataset and algorithm is available in the file: `/results/{dataset_id}/{improver_algorithm}.txt`.

The table below documents the performance metrics and characteristics of various algorithmic approaches.

| dataset_id   | improver_algorithm         | iteration # |   best value |
|--------------|----------------------------|-------------|--------------|
| i20          | LocalSearchImprover        |          83 |     37869.40 |
| i20          | SimulatedAnnealingImprover |         580 |     76782.70 |
| i20          | ALNSWrapper                |        9193 |    156641.30 |
|--------------|----------------------------|-------------|--------------|
| i30          | LocalSearchImprover        |         128 |     85071.20 |
| i30          | SimulatedAnnealingImprover |         667 |    162599.40 |
| i30          | ALNSWrapper                |        5290 |    119393.10 |
|--------------|----------------------------|-------------|--------------|
| i40          | LocalSearchImprover        |         169 |     95027.20 |
| i40          | SimulatedAnnealingImprover |         696 |    255312.20 |
| i40          | ALNSWrapper                |        3561 |    182828.10 |
|--------------|----------------------------|-------------|--------------|
| i50          | LocalSearchImprover        |         209 |    222911.30 |
| i50          | SimulatedAnnealingImprover |         671 |    488540.90 |
| i50          | ALNSWrapper                |        2441 |    326439.40 |
|--------------|----------------------------|-------------|--------------|
| i60          | LocalSearchImprover        |         238 |    243774.00 |
| i60          | SimulatedAnnealingImprover |         680 |    638195.30 |
| i60          | ALNSWrapper                |        1786 |    295738.60 |

The following graphs show the output after the first iteration of search, which may already include an identified improvement over the seed solution.

**I20** (UB 231132.00 / LB 9517.20)

<img src="./results/i20/LocalSearchImprover_iter.png" alt="LS" width="90%"/>
<img src="./results/i20/SimulatedAnnealingImprover_iter.png" alt="SA" width="90%"/>
<img src="./results/i20/ALNSWrapper_iter.png" alt="ALNS" width="90%"/>

Interestingly, ALNS cannot find improvements.
Local Search has the fewest iterations but the best performance.

**I30** (UB 499192.32 / LB 9630.72)

<img src="./results/i30/LocalSearchImprover_iter.png" alt="LS" width="90%"/>
<img src="./results/i30/SimulatedAnnealingImprover_iter.png" alt="SA" width="90%"/>
<img src="./results/i30/ALNSWrapper_iter.png" alt="ALNS" width="90%"/>

Note that Local Search has the fewest number of iterations but best performance.

**I40** (UB 522144.00 / LB 13171.19)

<img src="./results/i40/LocalSearchImprover_iter.png" alt="LS" width="90%"/>
<img src="./results/i40/SimulatedAnnealingImprover_iter.png" alt="SA" width="90%"/>
<img src="./results/i40/ALNSWrapper_iter.png" alt="ALNS" width="90%"/>

Note that Local Search has the fewest number of iterations but best performance.

**I50** (UB 863977.92 / LB 10093.20)

<img src="./results/i50/LocalSearchImprover_iter.png" alt="LS" width="90%"/>
<img src="./results/i50/SimulatedAnnealingImprover_iter.png" alt="SA" width="90%"/>
<img src="./results/i50/ALNSWrapper_iter.png" alt="ALNS" width="90%"/>

Note that Local Search has the fewest number of iterations but best performance.

**I60** (UB 1022151.22 / LB 2397.54 )

<img src="./results/i60/LocalSearchImprover_iter.png" alt="LS" width="90%"/>
<img src="./results/i60/SimulatedAnnealingImprover_iter.png" alt="SA" width="90%"/>
<img src="./results/i60/ALNSWrapper_iter.png" alt="ALNS" width="90%"/>

Note that Local Search has the fewest number of iterations but best performance.

## 6. Development & Deployment

### 6.1 Dependencies

- **Core:** Python 3.12+, Pydantic 2.12+, NumPy 2.3+
- **Optimisation:** ALNS 7.0+
- **Visualisation:** Matplotlib 3.10+
- **Utilities:** python-dotenv, NetworkX, Pandas, Pytest

### 6.2 Configuration (`.env`)

```
DATA_NODES_FILEPATH=/path/to/nodes.csv
TERMINATION_MAX_SECONDS=10
TERMINATION_MAX_ITERATIONS=10000
LOG_LEVEL=DEBUG
OUTPUT_DIR=/path/to/output
```

## 7. Future Work

Improvement ideas in methodology:
- Exact enumeration solver for tiny/small instances
- Tighter Lower Bound with careful relaxation of constraints
- Construction Heuristic: builds a route by always selecting the closest valid neighbour (first attempt failed)
- Constructor Heuristic: cluster-first-route-second approach
- Multiple seed candidates
- Metaheuristics: Tabu Search, Ant Colony, Genetic Algorithm
- Hyperparamter tuning (grid search, random search) and move all non-tunable parameters to `.env`
- Hybrid solution

Improvement ideas in implementation:
- Distributed computation
- GPU-accelerated distance matrix
