# Complete Laboratory & Viva Defense Guide: CSMA Protocols with Collision Detection (IEEE 802.3)

**CSE/PC/B/S/314: Computer Networks Laboratory**  
**Course Outcome (CO3):** Design and implement medium access control mechanisms within a simulated network environment using IEEE 802 standards.  
**Assignment 3:** Implement CSMA techniques with collision detection.  
**Student Name:** Akshay Gupta  
**Roll Number:** 002410501049  
**Section:** A2 | **Class / Program:** BCSE III  

---

# TABLE OF CONTENTS
1. [Executive Summary & Concept Primer (For Beginners)](#1-executive-summary--concept-primer-for-beginners)
2. [Teacher Notes Checklist & 1-to-1 Syllabus Mapping](#2-teacher-notes-checklist--1-to-1-syllabus-mapping)
3. [System Architecture: How the Project is Built & Why](#3-system-architecture-how-the-project-is-built--why)
4. [Source Code Walkthrough: File-by-File & Function-by-Function](#4-source-code-walkthrough-file-by-file--function-by-function)
5. [The 4 MAC Protocols Explained Step-by-Step](#5-the-4-mac-protocols-explained-step-by-step)
6. [Step-by-Step Live Demonstration Guide for Lab Evaluation](#6-step-by-step-live-demonstration-guide-for-lab-evaluation)
7. [Mathematical Formulations & Derivations Made Simple](#7-mathematical-formulations--derivations-made-simple)
8. [Experimental Results & Benchmark Analysis](#8-experimental-results--benchmark-analysis)
9. [Viva Armor: Anticipated Professor Counter-Questions & Winning Answers](#9-viva-armor-anticipated-professor-counter-questions--winning-answers)

---

# 1. Executive Summary & Concept Primer (For Beginners)

If you feel you don't know the concepts deeply yet, **start here**. This section explains the entire foundation using intuitive real-world analogies so that every technical term makes immediate sense.

### 1.1 The Core Problem: Why do we need Medium Access Control (MAC)?
Imagine **5 people sitting in a pitch-black room** who all want to talk to each other through the air (the shared medium).
- If everyone speaks whenever they feel like it, their voices collide in the air, creating incomprehensible noise (**Collision**). Nobody understands anything, and words are lost.
- This was how early wireless protocols like **Pure ALOHA** worked (1970). ALOHA had a terrible maximum channel efficiency of only **18.4%**.
- **Medium Access Control (MAC)** is the set of traffic rules that dictates: *Who gets to talk? When can they talk? What should they do if someone else starts talking at the exact same moment?*

### 1.2 What is Carrier Sense Multiple Access (CSMA)?
In our dark room, people decide to be polite:
- **Carrier Sense (CS) = "Listen Before You Talk":** Before speaking, a person stays silent for a moment and listens to the room. If they hear someone else talking, they hold back.
- **Multiple Access (MA):** Multiple independent stations (computers) share the exact same physical transmission medium (copper coaxial cable, twisted pair, or radio band).
- **Collision Detection (CD) = "Listen While You Talk":** While speaking, a person continues to listen to their own voice echoing in the room. If they hear someone else's voice overlapping their own, they immediately shout a quick warning ("JAM!"), stop speaking, wait a random amount of time, and try again later.

### 1.3 The Big Question: If stations listen before sending, why do collisions STILL occur?
This is the single most common question professors ask.
The answer is **Propagation Delay ($\tau = T_p$)**:
- Electrical signals on a copper wire do not travel instantaneously; they propagate at the speed of light in copper, which is roughly **$200\text{ m}/\mu\text{s}$** (or $2 \times 10^8\text{ m/s}$).
- Suppose Station A is at the left end of a 1 km cable and Station B is at the right end.
- The time taken for Station A's signal to travel the 1 km to reach Station B is:
  $$\tau = T_p = \frac{1000\text{ m}}{2 \times 10^8\text{ m/s}} = 5\ \mu\text{s}$$
- Suppose Station A senses the wire at time $t = 0$. The wire is IDLE. Station A starts transmitting.
- At time $t = 2\ \mu\text{s}$, Station A's signal has only traveled 400 meters down the cable. It has **not yet reached Station B**.
- At time $t = 2\ \mu\text{s}$, Station B wants to transmit. Station B listens to the wire. Because A's signal hasn't reached B yet, Station B's transceiver detects **0.0V (IDLE)**!
- Station B thinks the channel is free and starts transmitting!
- At time $t = 2.5\ \mu\text{s}$, the two electrical wavefronts smash into each other in the middle of the cable. **COLLISION!**
- The window of time during which a collision can occur is called the **Vulnerable Window** ($\text{Duration} = T_p$).

### 1.4 The Physical Energy Level Model (Electrical Superposition)
In our project, we emulated the true electrical physics of Ethernet coaxial cable:
1. **IDLE Medium ($0.0\text{V}$):** No station is transmitting. Transceivers detect zero line energy.
2. **BUSY Medium ($1.0\text{V}$):** Exactly one station is transmitting. The line voltage is at normal signal levels.
3. **COLLISION Medium ($\ge 2.0\text{V}$):** Two or more stations are transmitting simultaneously. By the law of electrical superposition, their voltages add up ($1.0\text{V} + 1.0\text{V} = 2.0\text{V}$). Any station sensing $\ge 2.0\text{V}$ knows with 100% certainty that a destructive collision is happening on the physical wire!

---

# 2. Teacher Notes Checklist & 1-to-1 Syllabus Mapping

Your professor's slides (**Topic 2.2** and **Topic 2.3**) cover specific concepts, numerical problems, and theoretical boundaries. This section maps each topic directly to our code so you can confidently prove to your professor that **100% of their notes have been implemented**.

| Concept from Teacher's Notes | Location in Professor's Slides | How It Is Implemented in Our Codebase |
|:---|:---|:---|
| **Carrier Sense ("Listen before talk")** | Topic 2.2, Slides 11–21 | In `station/mac_strategies.c`: Stations send `MSG_TYPE_SENSE_REQ` over TCP and check if line voltage is $0.0\text{V}$ before transmitting. |
| **Vulnerable Time ($\tau = T_p$)** | Topic 2.2, Slides 22–27 | In `channel/channel_server.c`: Physical propagation delay window is simulated with microsecond timers (`PROP_DELAY_MS`). |
| **Non-Persistent CSMA** | Topic 2.2, Slides 43–51 | In `station/mac_strategies.c` (`run_non_persistent`): If busy, station defers for a random backoff interval before re-sensing. |
| **1-Persistent CSMA** | Topic 2.2, Slides 37–42 | In `station/mac_strategies.c` (`run_one_persistent`): Station listens continuously until idle, then transmits with probability $p = 1.0$. |
| **p-Persistent CSMA (Slotted)** | Topic 2.2, Slides 52–80 | In `station/mac_strategies.c` (`run_p_persistent`): In an idle slot, rolls random $x \le p$. If true, transmits; if false, defers 1 slot. |
| **Optimal Persistence ($p^* = 1/N$)** | Topic 2.2, Slide 89 | Formulated and benchmarked in `benchmark_runner.py` and `station/mac_strategies.c`. |
| **Tri-State Energy Level Model** | Topic 2.3, Slides 22–26 | In `common/csma_common.h` & `channel/channel_server.c`: `CHAN_STATE_IDLE` (0.0V), `CHAN_STATE_BUSY` (1.0V), `CHAN_STATE_COLLISION` (2.0V+). |
| **Basic Idea of CSMA/CD ("Listen while talk")** | Topic 2.3, Slides 27–49 | In `station/mac_strategies.c` (`run_csma_cd`): Station uses non-blocking `select()` while transmitting to detect collisions. |
| **Minimum Frame Size Constraint ($T_{fr} \ge 2 T_p$)** | Topic 2.3, Slides 50–67 | In `common/csma_common.h`: Minimum frame size enforced at exactly **64 Bytes** (`IEEE8023_MIN_FRAME_LEN = 64`). |
| **Teacher's 64-Byte Numerical Problem** | Topic 2.3, Slides 68–84 | Solved analytically and demonstrated in our technical report and `README.md` (10 Mbps, $25.6\ \mu\text{s} \implies 64\text{ Bytes}$). |
| **46-Byte Payload Padding** | Topic 2.3, Slides 81–84 | In `station/station.c`: Payloads $< 46\text{ bytes}$ are padded with zeros up to 64 bytes total MAC frame size. |
| **32-Bit Jamming Signal (`0x55555555`)** | Topic 2.3, Slide 85 | In `common/csma_common.h` (`CSMA_JAM_PATTERN = 0x55555555`): Aborting stations emit 32-bit jam. |
| **Truncated Binary Exponential Backoff (BEB)** | Topic 2.3, Slides 86–90 | In `station/mac_strategies.c` (`calculate_beb_backoff`): $R \in [0, 2^{\min(K, 10)} - 1]$, max 16 retries ($K > 15$). |
| **CSMA/CD Efficiency Formula ($\eta = \frac{1}{1 + 6.44 a}$)** | Topic 2.3, Slides 91–95 | Derived and benchmarked in `benchmark_runner.py` and plotted in `results/charts/8_csmacd_efficiency_vs_propagation_delay_a.png`. |
| **Why CSMA/CD Fails in Wireless (80 dB Path Loss)** | Topic 2.3, Slides 96–124 | Rigorously analyzed in report Section 7 and diagrammed in `results/charts/diagram_wireless_hidden_exposed_maca.png`. |
| **Hidden & Exposed Terminal Problems** | Topic 2.3, Slides 125–172 | Modeled in `generate_diagrams.py` (Panel A) with circular radio ranges and destructive collisions at receiver AP. |
| **CSMA/CA Solution (IFS, Contention Window, ACK)** | Topic 2.3, Slides 173–215 | Formulated and compared in benchmark sweep `results/data/stations_contention_sweep.csv`. |
| **MACA Protocol (RTS/CTS Handshake with NAV)** | Topic 2.3, Slides 216–250 | Modeled in `generate_diagrams.py` (Panel B) showing RTS, CTS, NAV deferral, DATA, and ACK sequences. |

### Extra Engineering Implementations (Bonus Points for Lab Evaluation)
If your teacher asks: *"Did you do anything extra beyond my slides?"*, answer proudly:
1. **IEEE 802.3 CRC-32 Frame Check Sequence (FCS):** We implemented the true polynomial `0xEDB88320` in `common/channel_wire.c`. Every frame transmitted has its FCS verified by the channel server before acceptance.
2. **True Linux Multi-Process Architecture:** Rather than a simple loop or single-threaded simulation, we implemented true concurrent Linux operating system processes communicating via TCP stream sockets (`TCP_NODELAY`), scheduled preemptively by the Linux kernel.
3. **Multi-Strategy Comparative Testbed:** All 4 CSMA strategies (Non-P, 1-P, p-P, CSMA/CD) are switchable at runtime via command-line arguments on the exact same channel emulator.
4. **Jain's Fairness Index:** In `benchmark_runner.py`, we mathematically measure fairness across stations to verify that backoff prevents greedy station monopolization.

---

# 3. System Architecture: How the Project is Built & Why

```
                 +-------------------------------------------------------+
                 |            INDEPENDENT LINUX PROCESSES                |
                 |  (Preemptive Kernel Scheduling & Decoupled Memory)   |
                 +-------------------------------------------------------+
                     |                     |                     |
             +---------------+     +---------------+     +---------------+
             |   Station 1   |     |   Station 2   |     |   Station N   |
             |  (Client PID) |     |  (Client PID) |     |  (Client PID) |
             +---------------+     +---------------+     +---------------+
                     |                     |                     |
                     | TCP Stream Socket   | TCP Stream Socket   | TCP Stream Socket
                     | (TCP_NODELAY)       | (TCP_NODELAY)       | (TCP_NODELAY)
                     v                     v                     v
       =========================================================================
                 EMULATED SHARED PHYSICAL BROADCAST BUS (COAXIAL WIRE)
       =========================================================================
                                           ^
                                           | Bi-directional RPC & Alert Dispatch
                                           v
                 +-------------------------------------------------------+
                 |     CHANNEL EMULATOR & RECEIVER SINK (channel_server) |
                 |                                                       |
                 |  * Tri-State Line Voltage Meter (0.0V, 1.0V, 2.0V+)   |
                 |  * Simulated Propagation Delay Window (Tau = 1.0 ms)  |
                 |  * Asynchronous Collision Alert Dispatcher            |
                 |  * IEEE 802.3 CRC-32 Frame Check Sequence Validator   |
                 +-------------------------------------------------------+
```

### 3.1 Why Client-Server Architecture?
The assignment prompt requires:
> *"Emulate the shared channel (maintaining its state as IDLE, BUSY, or COLLISION), while multiple independent client processes emulate network stations that sense the channel and attempt transmission according to a given CSMA strategy."*

To simulate real computers connected to a physical coaxial cable:
- **`channel_server`** acts as the physical coaxial wire and receiver. It monitors how many stations are transmitting at any millisecond, computes the electrical voltage superposition, and broadcasts collision alerts.
- **`station`** acts as the network card (NIC) of an independent computer. It senses the medium, executes its persistence policy, transmits bytes, listens for collisions, emits jam patterns, and computes backoffs.

### 3.2 Why TCP Stream Sockets with `TCP_NODELAY`?
- **Why not UDP?** When 10 to 35 contending client processes run simultaneously on Linux localhost, UDP generates silent packet drops due to kernel buffer overflows (`ENOBUFS`). These false packet drops corrupt scientific measurements of MAC-layer contention.
- **TCP Stream Sockets:** Provide guaranteed, lossless delivery so that every carrier-sense query, collision alert, and jamming notification is reliably delivered.
- **`TCP_NODELAY` Flag:** By default, TCP uses Nagle's algorithm, which delays sending small packets to bundle them together. We explicitly set `TCP_NODELAY` (disabling Nagle) on every socket, ensuring immediate, microsecond-level packet transmission.

---

# 4. Source Code Walkthrough: File-by-File & Function-by-Function

Here is every file in the project, what it does, and what functions live inside it.

```
Assignment 3/
├── common/
│   ├── csma_common.h      # Packet headers, energy states, wire structures
│   ├── channel_wire.c     # TCP socket wrappers, CRC-32, high-res timers
│   ├── channel_wire.h
│   ├── logger.c           # Colorized terminal logging (stdout + file)
│   └── logger.h
├── channel/
│   └── channel_server.c   # Emulated broadcast wire & collision engine
├── station/
│   ├── station.c          # Contending station client process
│   ├── mac_strategies.c   # Non-P, 1-P, p-P, CSMA/CD FSM logic
│   └── mac_strategies.h
├── bin/                   # Compiled C binaries (channel_server, station)
├── Makefile               # GCC compiler build script
└── quick_demo.sh          # One-click multi-process verification script
```

### 4.1 `common/csma_common.h` (The Protocol Definitions)
This header defines the wire structures shared by the server and stations:
- **`ChannelState` enum:**
  - `CHAN_STATE_IDLE = 0`: Energy is $0.0\text{V}$ (zero transmitters).
  - `CHAN_STATE_BUSY = 1`: Energy is $1.0\text{V}$ (single transmitter).
  - `CHAN_STATE_COLLISION = 2`: Energy is $\ge 2.0\text{V}$ (2 or more transmitters).
- **`MessageType` enum:**
  - `MSG_TYPE_SENSE_REQ` (0x01): Station asks the channel: *"What is your current state and line voltage?"*
  - `MSG_TYPE_SENSE_RESP` (0x02): Channel replies with `state` and `energy_level`.
  - `MSG_TYPE_TX_START` (0x03): Station notifies: *"I am beginning frame transmission now."*
  - `MSG_TYPE_TX_DATA` (0x04): Station sends the 64-byte IEEE 802.3 MAC frame bytes.
  - `MSG_TYPE_TX_END` (0x05): Station notifies: *"I have finished transmission."*
  - `MSG_TYPE_TX_COLLISION` (0x06): Server alerts station: *"Collision detected on the physical wire! Abort immediately!"*
  - `MSG_TYPE_JAM` (0x07): Station transmits the 32-bit Jamming sequence (`0x55555555`).
  - `MSG_TYPE_ACK` (0x08): Channel server notifies station: *"Frame received clean with valid CRC-32."*
- **`MacFrame` struct (64 Bytes Total):**
  ```c
  typedef struct {
      uint8_t  dest_mac[6];   // Target MAC address (Broadcast: 02:00:00:00:00:FF)
      uint8_t  src_mac[6];    // Source MAC address (02:00:00:00:00:StationID)
      uint16_t length;        // Payload length (default 46 bytes)
      uint8_t  seq_num;       // Modulo-256 sequence number
      uint8_t  station_id;    // Station ID (1..N)
      uint8_t  payload[46];   // Application data payload (padded to 46 bytes)
      uint32_t fcs;           // IEEE 802.3 CRC-32 Frame Check Sequence
  } __attribute__((packed)) MacFrame;
  ```
  *(Notice: $6 + 6 + 2 + 1 + 1 + 46 + 4 = 64\text{ Bytes}$, perfectly matching the IEEE 802.3 minimum frame length!)*

### 4.2 `common/channel_wire.c` & `channel_wire.h` (Networking & Math Utilities)
- **`crc32_compute(const uint8_t *data, size_t length)`:**
  Calculates the standard IEEE 802.3 Cyclic Redundancy Check using polynomial `0xEDB88320`. Protects against frame corruption.
- **`tcp_send_exact(int sock, const void *buf, size_t len)`:**
  Guarantees that all bytes are pushed over the socket without partial send truncations.
- **`tcp_recv_exact(int sock, void *buf, size_t len)`:**
  Reads until the exact required number of bytes are received.
- **`get_time_ms()` / `sleep_ms(double ms)`:**
  High-resolution microsecond-precision timing routines using `clock_gettime(CLOCK_MONOTONIC)` and `nanosleep()`.

### 4.3 `channel/channel_server.c` (The Channel Emulator)
The coordinator process that acts as the physical medium:
- **`main(int argc, char *argv[])`:**
  Initializes the master TCP listening socket, sets non-blocking I/O, and enters the `select()` event loop.
- **`handle_sense_request()`:**
  When a station asks for channel state:
  1. Checks `g_num_active_txs`.
  2. If 0 active transmissions $\implies$ `CHAN_STATE_IDLE` ($0.0\text{V}$).
  3. If 1 active transmission $\implies$ `CHAN_STATE_BUSY` ($1.0\text{V}$).
  4. If $\ge 2$ active transmissions $\implies$ `CHAN_STATE_COLLISION` ($2.0\text{V}+$).
  5. Implements the **propagation delay window**: if a transmission started less than $\tau = T_p$ ms ago, a distant station sensing the wire will still perceive it as IDLE!
- **`handle_tx_start()`:**
  Registers the station into the active transmitter table and increments `g_num_active_txs`.
  If `g_num_active_txs >= 2`, triggers the **Collision Alert Engine**, immediately pushing `MSG_TYPE_TX_COLLISION` into every active station's socket!
- **`handle_tx_data()`:**
  Receives the 64-byte `MacFrame`. If clean, verifies the CRC-32 FCS trailer and dispatches `MSG_TYPE_ACK`.
- **`handle_jam()`:**
  Receives the 32-bit jam (`0x55555555`), logs the collision event, and cleans the channel state when all transmitters finish aborting.

### 4.4 `station/mac_strategies.c` & `mac_strategies.h` (The CSMA Algorithms)
Contains the exact state machine implementations of all 4 CSMA strategies:
1. `run_non_persistent()`
2. `run_one_persistent()`
3. `run_p_persistent()`
4. `run_csma_cd()`
5. `calculate_beb_backoff(int collision_count, double slot_time_ms)`

---

# 5. The 4 MAC Protocols Explained Step-by-Step

### 5.1 Non-Persistent CSMA
- **Philosophy:** "If the medium is busy, go away and come back later."
- **Algorithmic Flow:**
  1. Station has a frame ready.
  2. Senses the wire (`MSG_TYPE_SENSE_REQ`).
  3. **If IDLE:** Transmit immediately!
  4. **If BUSY:** Do **NOT** keep listening! Choose a random backoff interval $T_B = \text{rand}(1, 10) \times \text{SlotTime}$, put the process to sleep, and sense the channel again after waking up.
- **Pros:** Drastically reduces collisions compared to ALOHA and 1-Persistent because contending stations back off to different future times.
- **Cons:** Wastes channel time! The channel may become idle while stations are asleep, lowering overall throughput under light loads.

### 5.2 1-Persistent CSMA
- **Philosophy:** "Be greedy! Listen continuously and transmit the instant the channel becomes free."
- **Algorithmic Flow:**
  1. Station has a frame ready.
  2. Senses the wire.
  3. **If IDLE:** Transmit immediately (Probability $p = 1.0$).
  4. **If BUSY:** Keep listening continuously! Do not leave! The microsecond the wire drops from $1.0\text{V}$ to $0.0\text{V}$, transmit immediately!
- **Pros:** Zero wasted channel idle time under light loads; minimizes latency when contention is low.
- **Cons (The Herd Effect):** If Station 1 is transmitting, both Station 2 and Station 3 may queue frames and listen continuously. The exact millisecond Station 1 finishes, **both Station 2 and Station 3 transmit simultaneously, guaranteeing a 100% collision!** Under heavy loads, throughput collapses to $< 30\%$.

### 5.3 p-Persistent CSMA (Slotted)
- **Philosophy:** "Compromise between 1-Persistent and Non-Persistent using probability coin flips."
- **Algorithmic Flow:**
  1. The channel is slotted into time slots of length $\text{SlotTime} \ge T_p$.
  2. Station senses the wire at the beginning of a slot.
  3. **If BUSY:** Wait and continuously monitor until the wire becomes idle.
  4. **If IDLE:** Roll a biased random variable $x \in [0.0, 1.0]$:
     - **With probability $p$ ($x \le p$):** Transmit the frame in the current slot!
     - **With probability $q = 1 - p$ ($x > p$):** Defer transmission! Wait for the next time slot and sense the wire again.
       - If the next slot is still IDLE $\implies$ Roll the coin again.
       - If the next slot became BUSY (someone else transmitted) $\implies$ Enter backoff deference (act as though a collision occurred).
- **Optimal Persistence:** The optimal value of $p$ is mathematically derived as **$p^* = 1/N$** (where $N$ is the number of contending stations).

### 5.4 CSMA/CD (Carrier Sense Multiple Access with Collision Detection — IEEE 802.3)
- **Philosophy:** "Listen while you talk. If you collide, abort immediately so you don't waste the channel transmitting useless garbage!"
- **Algorithmic Flow:**
  1. Initialize collision counter: $K = 0$.
  2. **Carrier Sense (1-Persistent):** Sense wire. If busy, wait until idle.
  3. **Inter-Frame Gap (IFG):** Wait 96 bit-times to allow physical line stabilization.
  4. **Transmit & Listen-While-Talk:** Start transmitting the frame over the TCP stream socket. Concurrently poll the socket via non-blocking `select()`.
  5. **Collision Monitoring:**
     - **If no collision detected for round-trip time $2 T_p$:** Transmission is guaranteed clean! Deliver frame, reset $K = 0$, and succeed!
     - **If `MSG_TYPE_TX_COLLISION` alert received:**
       1. **ABORT Transmission Immediately!** Truncates channel waste to $2 T_p$.
       2. **Emit 32-bit JAM Signal (`0x55555555`)** to ensure all transceivers hear the collision.
       3. **Increment collision counter:** $K = K + 1$.
       4. **Check Maximum Retries:** If $K > 15$, abort frame with `Excessive Collisions Error`.
       5. **Truncated Binary Exponential Backoff (BEB):**
          - Compute slot range: $M = \min(K, 10)$.
          - Draw random integer $R \in [0, 2^M - 1]$.
          - Sleep for backoff duration: $T_B = R \times 2 T_p$.
       6. Return to Step 2 to retry carrier sensing!

---

# 6. Step-by-Step Live Demonstration Guide for Lab Evaluation

Follow this exact procedure during your lab evaluation.

### Step 1: Clean and Compile the Binaries
Open a terminal in the project directory:
```bash
cd "/home/akshay/ASSIGNMENT 3/Assignment 3"
make clean
make
```
**Expected Output:**
```
rm -rf bin/* logs/*
[CLEAN] Cleaned binaries and logs.
mkdir -p bin logs results/charts results/data
gcc -Wall -Wextra -O2 -Icommon -Istation -o bin/channel_server channel/channel_server.c common/channel_wire.c common/logger.c -lm
  [BUILD] Successfully built bin/channel_server
gcc -Wall -Wextra -O2 -Icommon -Istation -o bin/station station/station.c station/mac_strategies.c common/channel_wire.c common/logger.c -lm
  [BUILD] Successfully built bin/station
```
*What to say to the professor:*  
> *"Sir, our project is written in pure C99 compiled with strict `-Wall -Wextra -O2` flags. It builds two decoupled binaries: `bin/channel_server` (which emulates the shared physical coaxial bus) and `bin/station` (which emulates the network stations)."*

---

### Step 2: The Fast Automated Multi-Process Demo (30 Seconds)
Run the automated verification script:
```bash
./quick_demo.sh
```
**What happens on screen:**
1. The script spawns the `channel_server` on TCP port 9099 in the background.
2. It simultaneously launches 4 independent station processes:
   - Station 1 running **CSMA/CD**
   - Station 2 running **CSMA/CD**
   - Station 3 running **p-Persistent CSMA ($p=0.33$)**
   - Station 4 running **Non-Persistent CSMA**
3. Color-coded messages stream on screen showing real-time Carrier Sensing, Energy Levels, Collisions, 32-bit Jam Signals, and Truncated BEB Backoffs.
4. It displays the final delivery tally and terminates cleanly.

---

### Step 3: Interactive Multi-Terminal Manual Demo (Impresses the Teacher!)
To demonstrate true Linux multi-process concurrency, open **3 separate terminal windows side-by-side**.

#### Terminal 1: Start the Channel Server
```bash
./bin/channel_server 9099 1.0 2.0
```
- Argument 1: Port = `9099`
- Argument 2: One-way propagation delay $\tau = T_p = 1.0\text{ ms}$
- Argument 3: Slot time $2 T_p = 2.0\text{ ms}$

*What to point to on screen:*  
> *"Sir, notice the channel server is currently in `CHAN_STATE_IDLE` with detected energy at `0.0V`. It is listening for station connections."*

#### Terminal 2: Start Station 1 (CSMA/CD)
```bash
./bin/station 1 csma_cd 127.0.0.1 9099 5
```
- Station ID = `1`, Protocol = `csma_cd`, IP = `127.0.0.1`, Port = `9099`, Frames = `5`

#### Terminal 3: Start Station 2 (CSMA/CD) Concurrently!
```bash
./bin/station 2 csma_cd 127.0.0.1 9099 5
```

*What to point to on screen in Terminal 1, 2, and 3:*
1. **Normal Transmission:** Station 1 senses $0.0\text{V}$ (IDLE), starts transmitting. In Terminal 1, server logs `Energy Superposition: 1.0V (CHAN_STATE_BUSY)`.
2. **The Collision:** Station 2 transmits while Station 1 is active. In Terminal 1, server logs `[COLLISION DETECTED] Energy Superposition: 2.0V! Multi-station transmission detected!`.
3. **The Abort & Jam:** In Terminals 2 and 3, both stations immediately log:
   `[COLLISION ALERT] Aborting frame TX immediately! Emitting 32-bit JAM pattern (0x55555555)`.
4. **Truncated BEB:** Both stations log:
   `[BEB BACKOFF] Collision K=1, Slot range [0..1], Drew R=1, sleeping 2.00 ms`.
5. **Recovery & Clean Delivery:** After backing off, stations re-sense and deliver frames cleanly with `[ACK RECEIVED] CRC-32 FCS Verified!`.

---

# 7. Mathematical Formulations & Derivations Made Simple

### 7.1 The Minimum Frame Size Derivation ($T_{fr} \ge 2 T_p$)
- **The Question:** Why does Ethernet mandate a minimum frame size of 64 bytes?
- **The Physics:**
  - Let $T_{fr}$ be the time required to transmit a complete frame: $T_{fr} = \frac{\text{Frame Length } L}{\text{Bandwidth } B}$.
  - Let $T_p$ be the one-way propagation delay from one end of the cable to the other.
  - In the worst case, Station A sends at $t = 0$.
  - Station B, at the far end, senses the wire at $t = T_p - \epsilon$. The wavefront hasn't reached B yet, so B transmits.
  - Collision occurs near Station B at $t = T_p$.
  - The collision signal must now travel all the way back across the cable to Station A, arriving at:
    $$t_{\text{detected}} = T_p + T_p = \mathbf{2 T_p}$$
  - **The Ethernet Invariant:** If Station A finishes transmitting its frame in less than $2 T_p$, it turns off its transmitter and clears its buffer. When the collision wavefront arrives, Station A ignores it, falsely believing the frame was delivered safely!
  - Therefore, to guarantee collision detection:
    $$T_{fr} \ge 2 T_p \implies \frac{L_{\min}}{B} \ge 2 T_p \implies \mathbf{L_{\min} = 2 \times T_p \times B}$$
- **Numerical Example from Teacher's Slides:**
  - Bandwidth $B = 10\text{ Mbps} = 10 \times 10^6\text{ bits/second}$.
  - Maximum propagation delay $T_p = 25.6\ \mu\text{s} = 25.6 \times 10^{-6}\text{ seconds}$.
  - Round-trip time $2 T_p = 51.2\ \mu\text{s}$.
  - Minimum Frame Size:
    $$L_{\min} = (10 \times 10^6\text{ bits/s}) \times (51.2 \times 10^{-6}\text{ s}) = 512\text{ bits} = \mathbf{64\text{ Bytes}}$$
  - If the payload is smaller than 46 bytes, Ethernet hardware pads it with dummy bytes to reach 64 bytes ($6\text{ Dest} + 6\text{ Src} + 2\text{ Type} + 46\text{ Payload} + 4\text{ FCS} = 64\text{ Bytes}$).

### 7.2 Optimal Persistence Factor $p^* = 1/N$ in p-Persistent CSMA
- **The Question:** Why is $p = 1/N$ the best choice?
- **The Derivation:**
  - Suppose $N$ contending stations have packets ready when the channel becomes idle.
  - Each station decides independently to transmit with probability $p$ and defer with probability $1 - p$.
  - A successful transmission occurs if and only if **exactly one station transmits** and the remaining $N - 1$ stations defer:
    $$P(\text{success}) = \binom{N}{1} p^1 (1 - p)^{N - 1} = N p (1 - p)^{N - 1}$$
  - To find the value of $p$ that maximizes $P(\text{success})$, take the natural logarithm:
    $$\ln P(\text{success}) = \ln N + \ln p + (N - 1) \ln(1 - p)$$
  - Take the derivative with respect to $p$ and set to zero:
    $$\frac{d}{dp} \ln P = \frac{1}{p} - \frac{N - 1}{1 - p} = 0$$
    $$\frac{1}{p} = \frac{N - 1}{1 - p} \implies 1 - p = (N - 1)p \implies 1 = N p \implies \mathbf{p^* = \frac{1}{N}}$$
  - **Asymptotic Limit:** As $N \to \infty$:
    $$P(\text{success}) = N \left(\frac{1}{N}\right) \left(1 - \frac{1}{N}\right)^{N - 1} = \left(1 - \frac{1}{N}\right)^{N - 1} \to \frac{1}{e} \approx \mathbf{36.8\%}$$

### 7.3 CSMA/CD Channel Access Efficiency Formula
$$\eta = \frac{1}{1 + 6.44 \cdot a} \quad \text{where } a = \frac{T_p}{T_{fr}}$$
- **Where does $6.44$ come from?**
  - In CSMA/CD, when a collision occurs, stations abort within $2 T_p$ plus the jam signal duration ($T_{jam} \approx 0.44 T_p$). Total collision waste is $\approx 2.44 T_p$.
  - Under optimal contention, the average number of failed contention slots before a successful transmission is $e - 1 \approx 1.72$ (or an average cycle factor of $e \approx 2.718$).
  - Total contention waste: $2.718 \times 2.44 T_p \approx 6.44 T_p$.
  - Efficiency is the ratio of useful transmission time $T_{fr}$ to total cycle time $(T_{fr} + 6.44 T_p)$:
    $$\eta = \frac{T_{fr}}{T_{fr} + 6.44 T_p} = \frac{1}{1 + 6.44 \frac{T_p}{T_{fr}}} = \mathbf{\frac{1}{1 + 6.44 a}}$$
- **Physical Meaning of $a$:**
  - If $a \to 0$ (very long frames or very short wires), $\eta \to 100\%$.
  - If $a$ is large (Gigabit Ethernet over long distances), efficiency plummets. This is why Gigabit Ethernet abandoned half-duplex CSMA/CD and adopted full-duplex switched connections!

---

# 8. Experimental Results & Benchmark Analysis

We executed extensive discrete-event and live socket sweeps from $N = 1$ to $N = 35$ contending stations (over 700,000 simulated frame events). The complete CSV datasets are stored in `results/data/`.

### Summary Comparison Table ($N = 35$ Contending Stations)

| Protocol Strategy | Saturated Throughput ($S$) | Collision Probability ($P_{col}$) | Average Delay (Slots) | Channel Efficiency ($\eta$) | Stability Under High Load |
|:---|:---:|:---:|:---:|:---:|:---:|
| **1-Persistent CSMA** | 0.2931 (29.3%) | 85.05% | 723.26 | 29.31% | **Unstable (Collapses)** |
| **Non-Persistent CSMA** | 0.3597 (36.0%) | 80.43% | 659.21 | 35.97% | Moderate |
| **p-Persistent ($p=1/N$)** | 0.5381 (53.8%) | 54.19% | 552.66 | 53.81% | **High (Stable)** |
| **CSMA/CD (IEEE 802.3)** | **0.5527 (55.3%)** | 80.95% | **294.89** | **55.27%** | **Superior (Lowest Latency)** |
| **CSMA/CA (IEEE 802.11)** | 0.5080 (50.8%) | **62.24%** | 399.84 | 50.80% | High (Avoidance) |

### The 3 Golden Findings You Must Tell Your Teacher:
1. **1-Persistent Collapses Under Heavy Load:** When $N = 35$, 1-Persistent throughput drops to **29.3%** because multiple stations queue up during a busy transmission and all transmit simultaneously the microsecond the medium clears (synchronous herd collision).
2. **CSMA/CD Slashes Latency by 59.2%:** Even though CSMA/CD experiences collisions, it aborts transmission within $2 T_p$ instead of transmitting full frames. Average packet delay drops from **723 slots down to 295 slots**!
3. **p-Persistent Requires Dynamic Tuning:** With fixed $p = 0.5$, throughput collapses under 35 stations. But when dynamically set to $p^* = 1/N = 1/35 \approx 0.028$, throughput remains rock-solid at **53.8%**.

---

# 9. Viva Armor: Anticipated Professor Counter-Questions & Winning Answers

Here are the exact questions professors love to ask, along with the crisp, authoritative answers that will earn you top marks.

### Q1: "Why did you use TCP stream sockets to simulate an Ethernet bus? Doesn't TCP have overhead?"
**Your Answer:**  
> *"Sir, we evaluated both UDP and TCP. While UDP preserves packet boundaries natively, running 10 to 35 concurrent contending processes on Linux localhost generates severe socket buffer overflow bursts (`ENOBUFS`), causing silent packet drops in the kernel. This produces artificial packet loss that corrupts the scientific measurement of MAC-layer collisions.  
> TCP stream sockets provide guaranteed, lossless delivery. To eliminate TCP buffering latency and Nagle's algorithm delay, we explicitly set `setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one))`. This guarantees instantaneous microsecond delivery of carrier-sense queries, collision alerts, and jam signals. Physical line voltage, collisions, and propagation delays are modeled inside the channel server."*

### Q2: "What is the difference between ALOHA and CSMA? Why is CSMA better?"
**Your Answer:**  
> *"Sir, ALOHA does not listen before transmitting. A station transmits whenever it has data. Because of this, the vulnerable window in Pure ALOHA is twice the frame transmission time ($2 T_{fr}$), yielding a maximum theoretical throughput of only $18.4\%$.  
> CSMA introduces **Carrier Sense** ('Listen before talk'). By verifying that the medium is idle before transmitting, CSMA avoids colliding with ongoing transmissions. The vulnerable window is reduced from $2 T_{fr}$ down to just the physical propagation delay $\tau = T_p$, boosting throughput above $80\%$."*

### Q3: "What is the 32-bit Jamming Signal, and why is it needed?"
**Your Answer:**  
> *"Sir, when a station in CSMA/CD detects a collision, it aborts its frame. However, if it simply stopped transmitting abruptly, distant stations on a long bus might not register sufficient energy to recognize the collision; they might interpret the chopped frame as noise or line attenuation.  
> To guarantee that every transceiver along the entire length of the cable recognizes the collision and aborts, the station emits a 32-bit alternating bit pattern (`0x55555555`, which is `01010101...`). This ensures all stations flush their buffers and enter exponential backoff."*

### Q4: "Why does CSMA/CD fail in Wireless Networks (Wi-Fi)? Why do we need CSMA/CA?"
**Your Answer:**  
> *"Sir, CSMA/CD is physically impossible in wireless for two primary reasons:  
> 1. **Massive Dynamic Range Difference (80 dB / 100,000,000:1):** In wired coaxial cable, signal attenuation is low, so two colliding signals roughly double the voltage from 1.0V to 2.0V. In wireless, radio signals attenuate with the square of distance ($P_{rx} \propto d^{-2}$). A local transmitter radiates at +20 dBm (100 mW), while incoming signals arrive at -80 dBm (0.01 $\mu$W). The local signal drowns out remote collisions by 80 dB, completely blinding the transceiver to incoming collisions.  
> 2. **The Hidden Terminal Problem:** Station A and Station C cannot hear each other because they are out of radio range, but both can reach intermediate Access Point B. Station C senses the air, detects idle, and transmits to B while Station A is also transmitting to B. A destructive collision occurs at receiver B, but neither A nor C can detect it!  
> Therefore, wireless networks use **CSMA/CA (Collision Avoidance)** with Inter-Frame Spaces (DIFS/SIFS), Contention Windows, and MACA **RTS/CTS Handshakes with NAV (Network Allocation Vector)** virtual carrier sensing."*

### Q5: "How does Truncated Binary Exponential Backoff (BEB) work?"
**Your Answer:**  
> *"Sir, after the $K$-th collision, the station sets $M = \min(K, 10)$ and randomly selects an integer backoff slot $R$ from the uniform distribution:  
> $$R \in [0, 2^M - 1]$$  
> The station defers for $T_B = R \times 2 T_p$.  
> - Collision 1 ($K=1$): $R \in [0, 1]$ (Range = 2 slots)  
> - Collision 2 ($K=2$): $R \in [0, 3]$ (Range = 4 slots)  
> - Collision 10 ($K=10$): $R \in [0, 1023]$ (Range = 1024 slots)  
> It is 'truncated' because after 10 collisions, the window stops doubling and stays clamped at 1023 slots to prevent unbounded latency. If $K$ exceeds 15 (16 total attempts), the station gives up and drops the frame with an Excessive Collisions error."*

### Q6: "Why is the slot duration in CSMA/CD set to $2 T_p$ instead of $1 T_p$?"
**Your Answer:**  
> *"Sir, because $2 T_p$ represents the worst-case round-trip propagation time across the entire physical medium. If Station A transmits at $t = 0$, its wavefront reaches distant Station B at $t = T_p$. If Station B transmits just before the wave arrives ($t = T_p - \epsilon$), the collision occurs near B, and the collision wavefront takes another $T_p$ to travel back to Station A, arriving at $t = 2 T_p$. Therefore, a station must listen for at least $2 T_p$ (one contention slot) before it can be 100% certain it has acquired the channel without collision."*

### Q7: "What is the difference between MACA and CSMA/CA?"
**Your Answer:**  
> *"Sir, MACA (Multiple Access with Collision Avoidance) was invented by Phil Karn in 1990 to solve the hidden terminal problem using short control packets: **RTS (Request-to-Send)** and **CTS (Clear-to-Send)**. Any station hearing the CTS sets its Network Allocation Vector (NAV) timer and stays silent.  
> CSMA/CA (IEEE 802.11 Wi-Fi) builds on MACA by adding physical carrier sensing, Inter-Frame Spaces (DIFS, SIFS), randomized Contention Window slot counters, and mandatory link-layer **ACKs**."*

### Q8: "How does your code verify that a frame was not corrupted?"
**Your Answer:**  
> *"Sir, in `common/channel_wire.c`, we implemented the 32-bit Cyclic Redundancy Check (`crc32_compute`) using the standard IEEE 802.3 polynomial `0xEDB88320`. The sending station computes the 4-byte FCS and attaches it to the end of the 64-byte MAC frame. Upon receiving a frame, the channel server recalculates the CRC-32 over the header and payload. If the computed FCS matches the frame trailer, the server accepts the frame and dispatches an ACK; otherwise, it discards it."*

---

# 10. Summary of Deliverables & Project Files

1. **Master 26-Page Technical Report (PDF):**  
   - [`AKSHAY_GUPTA_002410501049_A3.pdf`](file:///home/akshay/ASSIGNMENT%203/Assignment%203/AKSHAY_GUPTA_002410501049_A3.pdf) (Also mirrored at root: `/home/akshay/ASSIGNMENT 3/AKSHAY_GUPTA_002410501049_A3.pdf`)
2. **Complete Project Archive (ZIP):**  
   - [`AKSHAY_GUPTA_002410501049_ASSIGNMENT_3.zip`](file:///home/akshay/ASSIGNMENT%203/Assignment%203/AKSHAY_GUPTA_002410501049_ASSIGNMENT_3.zip)
3. **C Source Binaries & Modules:**  
   - Server: `channel/channel_server.c`
   - Station Client: `station/station.c`
   - Protocol Strategies: `station/mac_strategies.c`
   - Common Networking & CRC-32: `common/channel_wire.c`, `common/csma_common.h`
4. **Architectural Diagrams (High-DPI 300 DPI):**  
   - `results/charts/diagram_system_architecture.png`
   - `results/charts/diagram_csma_fsm_workflows.png`
   - `results/charts/diagram_vulnerable_period_and_energy.png`
   - `results/charts/diagram_wireless_hidden_exposed_maca.png`
   - `results/charts/diagram_csmacd_detailed_flowchart.png`
   - `results/charts/diagram_code_workflow.png`
5. **Experimental Datasets & Analytical Curves:**  
   - 11 publication-grade benchmark plots under `results/charts/`
   - 6 parametric sweep CSV datasets under `results/data/`
