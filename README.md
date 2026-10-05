# Concurrent Multi-Threaded CSMA & CSMA/CD Simulation (IEEE 802.3)
**Department of Computer Science & Engineering, Jadavpur University**  
**Course Outcome CO3: Medium Access Control Protocols & Multi-Threaded Concurrency**

---

## 1. Project Overview

This project provides a complete, high-performance C implementation and empirical evaluation of **Carrier Sense Multiple Access (CSMA)** MAC protocols, modeled using **concurrent POSIX station threads (`pthreads`)** and a **thread-synchronized physical broadcast medium**.

### Implemented MAC Protocols
1. **Non-Persistent CSMA:** Senses the channel. If busy, immediately defers for a uniform random backoff interval without persistent listening. If idle, transmits immediately.
2. **1-Persistent CSMA:** Continuously monitors the channel when busy ("greedy" sensing). As soon as the channel becomes idle, transmits immediately with probability $p = 1.0$.
3. **p-Persistent CSMA (Slotted):** Senses the channel. When idle, transmits in the current mini-slot with probability $p$, or defers by 1 slot ($2\tau$) with probability $1 - p$.
4. **CSMA/CD (IEEE 802.3 Standard):** 1-persistent carrier sense with **Listen-While-Talk (LWT)** preemption, constructive voltage superposition collision detection ($0.0\text{V} \implies$ IDLE, $1.0\text{V} \implies$ BUSY, $\ge 2.0\text{V} \implies$ COLLISION), **32-bit Jamming Signal** (`0x55555555`), and **Truncated Binary Exponential Backoff (BEB)**.

> **Key Protocol Isolation Rules:**
> - **Jamming Signal:** Emitted **strictly in CSMA/CD** upon detecting $V \ge 2.0\text{V}$. Non-CD strategies do NOT emit jam patterns.
> - **Truncated BEB:** Applied **strictly in CSMA/CD** ($k = \min(\text{attempts}, 10)$, $R \in [0, 2^k - 1]$, $T_{\text{backoff}} = R \times T_{\text{slot}}$). Non-CD strategies use uniform random backoff over a fixed window ($R \in [1, 16]$ slots).

---

## 2. Directory Structure

```
ASSIGNMENT 3/
├── AKSHAY_GUPTA_002410501049_A3.pdf       # The complete 29-page formal lab report
├── Makefile                               # Clean C compiler build script
├── README.md                              # This documentation
├── csma_sim.c                             # Clean, concurrent multi-threaded CSMA simulator
├── interactive_menu.sh                    # Interactive Multi-Threaded launcher & menu
├── run_high_scale_simulation.py           # High-scale simulation & chart generator
├── generate_report.py                     # ReportLab PDF report generation engine
├── generate_diagrams.py                   # High-res architectural flowcharts & diagrams
├── generate_charts.py                     # Matplotlib empirical performance graphs
├── generate_math_cards.py                 # Formula cards generator
├── common/
│   ├── csma_common.h                      # Protocol constants, enums, frame structures
│   ├── channel_wire.h / channel_wire.c    # CRC-32 & microsecond timing utilities
│   └── logger.h / logger.c                # Thread-safe event logger
└── results/
    ├── charts/                            # Generated 300 DPI figures & flowcharts
    │   └── math/                          # Rendered LaTeX mathematical formula cards
    └── data/                              # Benchmark CSV datasets
```

---

## 3. Architecture & Thread Synchronization

### Concurrent Station Threads (`pthread_create`)
* When running with $N$ stations, the coordinator initializes the shared broadcast bus and spawns $N$ concurrent station worker threads executing simultaneously:
  ```c
  pthread_create(&threads[i], NULL, station_worker_thread, &args[i]);
  ```

### Shared Physical Channel & Voltage Superposition
* The shared coaxial channel tracks instantaneous transmission count and voltage:
  - $0.0\text{V} \implies$ IDLE (0 transmitters)
  - $1.0\text{V} \implies$ BUSY (1 active transmitter)
  - $\ge 2.0\text{V} \implies$ COLLISION (2+ concurrent transmitters)

### Synchronization Primitives
* Stations coordinate via standard POSIX mutexes and condition variables:
  ```c
  pthread_mutex_lock(&bus->lock);
  pthread_cond_wait(&bus->idle_cond, &bus->lock);
  pthread_mutex_unlock(&bus->lock);
  ```

---

## 4. How to Compile & Run

### 1. Build the Binary
```bash
make all
```
* Compiles `csma_sim.c` with `-O2 -pthread -Wall -Wextra` into `bin/csma_sim`.

### 2. Run the Interactive C Simulator (Zero CLI Arguments)
You can directly run the simulator or use `make run`:
```bash
make run
# or directly:
./bin/csma_sim
```
The program presents a full, interactive terminal menu:
```
==========================================================================
     CSE/PC/B/S/314: MULTI-THREADED CSMA & CSMA/CD SIMULATOR MENU        
   Jadavpur University - Department of Computer Science & Engineering    
==========================================================================
1) Run Multi-Threaded Simulation (Interactive Configuration)
2) Run Station Contention Sweep across Station Counts (N = 2 to 32)
3) Exit
```
* **Option 1 (Interactive Run):** Interactively prompts for MAC Strategy (CSMA/CD, 1-Persistent, Non-Persistent, p-Persistent), number of stations ($2 \to 64$), frames per station ($1 \to 50$), and probability $p$ (if applicable).
* **Option 2 (Contention Sweep):** Automatically sweeps station thread counts across $N \in \{2, 4, 8, 16, 24, 32\}$ and appends live metrics to `results/data/live_c_benchmarks.csv`.
* **Option 3 (Exit):** Cleanly terminates.

### 3. Top-Level Launcher Menu
```bash
./interactive_menu.sh
```
Provides quick access to run the C simulation, re-run high-scale Python sweeps, or recompile the formal PDF report.

---

## 5. Performance Metrics & Analysis

Every multi-threaded simulation execution logs microsecond-level timing and prints a complete performance breakdown:
* **Per-Station Breakdown:** Station ID, frame attempts, successful deliveries, collisions, average latency (ms), and total backoff time (ms).
* **Global Bus Metrics:** Total attempts, delivered frames, total collisions detected, total 32-bit jam signals, throughput (bps / kbps), channel efficiency ($\eta\%$), and delivery success ratio.
* **Automated CSV Logging:** Every run automatically records its metrics into `results/data/live_c_benchmarks.csv`.
