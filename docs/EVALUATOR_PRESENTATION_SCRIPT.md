# LaneRush Evaluator Demonstration Guide & Presentation Script

This document provides the step-by-step procedure and talking script to demonstrate LaneRush to evaluators, professors, and technical reviewers.

---

## 1. Setup Architecture: The Dual-Screen Demonstration

Evaluators require two core proofs:
1. **Microscopic Reality (SUMO-GUI):** Real 2D vehicle physics, lane queues building up, signal bars turning red/yellow/green, and an emergency vehicle cruising through without stopping.
2. **AI Control Telemetry (React Dashboard at `http://127.0.0.1:8000`):** Real-time lane rush scoring ($W_{\text{count}}, W_{\text{halt}}, W_{\text{age}}$), hysteresis release, upstream emergency lookahead, dynamic queue pre-clearing, and network-wide fairness.

### Command to Launch the Demonstration:
Open two PowerShell terminals:

#### Terminal 1 — Start the React AI Dashboard:
```powershell
.\lanerush.ps1 ui
```
*Open `http://127.0.0.1:8000` in Google Chrome or Microsoft Edge.*

#### Terminal 2 — Run the Microscopic Visual Simulation (Side-by-Side):
```powershell
.\lanerush.ps1 run --gui
# Or:
python starter.py --gui
```
*Position SUMO-GUI on the left half of your monitor and the React Dashboard on the right half.*

---

## 2. Walkthrough Script for the Evaluator

When presenting, you can either play the live simulation or use the **"Presentation Guide"** button in the React Dashboard to jump directly to each key timestamp.

### Feature 1: Traffic Rush-Based Dynamic Signal Release ($t=15\text{s} - 35\text{s}$)
- **What to show on screen:**
  - In React UI: Click **"Jump to t=25s"** (or watch Junction A1 & B1).
  - Observe the dynamic queue dots on North-South vs East-West arms, and the **Rush Scores** (`NS` and `EW`) in the Junction Inspector.
- **What to explain to the evaluator:**
  > *"Traditional traffic signals operate on fixed cyclic timers (e.g., 42s North-South, 42s East-West), causing empty lanes to hold green while cars wait needlessly on busy cross-streets.*
  > *In LaneRush, every second each signal computes a multi-factor rush score:*
  > $$\text{Score} = W_{\text{count}}\cdot \text{count} + W_{\text{halt}}\cdot \text{halting} + W_{\text{age}}\cdot \text{max\_wait}$$
  > *When congestion builds up on the cross-street, the hysteresis engine triggers:*
  > $$\text{Score}_{\text{other}} > 1.2 \cdot \text{Score}_{\text{cur}} + 1.0$$
  > *This dynamically transfers the green phase to the rush lane while preventing high-frequency signal flickering."*

---

### Feature 2: 4 Passenger Cars Stuck at Red Signal ($t=38\text{s}$)
- **What to show on screen:**
  - Click **"Jump to t=38s"**.
  - Direct the evaluator's attention to **Junction A1 on Row 1 (Main Corridor)**.
  - Notice the **"4 CARS STUCK AT RED"** queue on the western approach (`left1A1_0`).
- **What to explain to the evaluator:**
  > *"Here is the critical failure mode of existing emergency vehicle preemption systems:*
  > *Even if you turn the light green when the ambulance reaches the intersection, stationary passenger cars trapped at the red light have nowhere to go and block the ambulance.*
  > *LaneRush anticipates this bottleneck through dynamic queue-aware pre-clearing."*

---

### Feature 3: Emergency Vehicle Pre-Clearing & Immediate Cross-Traffic Halting ($t=42\text{s}$)
- **What to show on screen:**
  - Click **"Jump to t=42s"**.
  - Ambulance `EV0` appears with flashing siren icon.
  - Upstream signal indicator badges switch to `🚨 PRE-CLEAR`.
  - In SUMO-GUI, the North-South signal changes from Green $\to$ Yellow $\to$ Red.
- **What to explain to the evaluator:**
  > *"At $t=40\text{s}$, emergency vehicle EV0 is detected on the approach. Our lookahead algorithm computes the arrival time at the next 3 junctions using:*
  > $$\text{ETA} = \frac{\text{distance}}{\min(v_{\text{speed\_limit}}, v_{\text{free\_flow}})}$$
  > *Pre-clearing is triggered when:*
  > $$\text{ETA} \le 12\text{s} + 2\text{s} \times \text{halted\_cars}$$
  > *Notice the safety invariant:* **All adjacent North-South cross-traffic is immediately brought to a halt via a safe yellow clearance phase**, preventing dangerous intersection conflicts before EV0 arrives."*

---

### Feature 4: Pre-Flush Queue Clearance & Zero-Delay Green Wave ($t=48\text{s}$)
- **What to show on screen:**
  - Click **"Jump to t=48s"**.
  - The 4 stuck passenger cars receive green early and accelerate out of the intersection.
  - When `EV0` reaches Junction A1 at $t=50\text{s}$, the lane is completely empty.
  - `EV0` cruises straight through A1, B1, and C1 at full speed (34 km/h) without braking.
- **What to explain to the evaluator:**
  > *"Because the 4 queued cars were flushed out ahead of time, EV0 experiences **0.0 seconds of waiting time**. Across the network, EV transit duration drops from 190.4s down to 97.0s — a **49.1% reduction in emergency response time**."*

---

### Feature 5: Starvation Prevention & Fairness Recovery ($t=68\text{s}$)
- **What to show on screen:**
  - Click **"Jump to t=68s"**.
  - Once `EV0` clears Junction A1, the corridor hold expires.
  - The signal immediately prioritizes the North-South cross-traffic.
- **What to explain to the evaluator:**
  > *"Many corridor systems cause severe gridlock on cross-streets after an emergency vehicle passes.*
  > *In LaneRush, the aging term $W_{\text{age}} \cdot \text{max\_wait}$ accumulates on waiting vehicles, giving them elevated priority as soon as the corridor clears.*
  > *This guarantees network-wide stability and achieves a verified **Jain Fairness Index of 0.95**."*

---

## 3. Evaluator FAQ & Quick Answers

- **Q: Why was Corridor Overrides showing 0 in some runs?**
  - **A:** LaneRush includes multiple experimental baselines (`fixed`, `fixed_tuned`, `adaptive_noaging`, `adaptive`, and `adaptive_corridor`). When testing `adaptive` alone, the corridor module is intentionally disabled as an ablation study. Selecting `adaptive_corridor` enables full green corridor pre-clearing with 4 pre-clear triggers.
- **Q: Does this require internet or external cloud APIs?**
  - **A:** No. The entire system runs 100% locally on your machine via Python, SUMO/TraCI, FastAPI, and Vite React.
- **Q: What happens if camera detection is noisy or vehicles are missed?**
  - **A:** In Phase 8, we integrated a `NoisyEmulator` that tests binomial thinning and Poisson phantom detections; the controller remains stable down to 70% detection recall.
