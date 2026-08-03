## Deployment-Time Estimation / Observer / Online Adaptation — Koopman-Based Approaches

### 1. EVOLVER (Evolutionary Model-Based Disturbance Observer)

**Mechanism.** EVOLVER uses the Koopman operator to lift internal+external disturbance dynamics onto a space where an "evolutionary" model-based observer estimates the disturbance recursively, explicitly modeled on a two-phase biological response (fast transient reaction, then gradual steady-state adaptation to the estimated disturbance). It plugs in as a real-time disturbance estimator that feeds forward into the controller (state-estimation/compensation role, not a reward or training-time signal) — output is a disturbance estimate, not a new dynamics model per se. The observer carries a provable convergence guarantee under stated (optimal) conditions.

**Evidence.** Tested on a real quadrotor (indoor+outdoor flight), a robotic manipulator, and a simulated irregular free-flying object. Authors claim superiority over unspecified state-of-the-art model-based and learning-based disturbance-estimation baselines (exact numeric deltas not extracted from the accessible source — full IEEE T-RO text would be needed for the table). Critically for deployment: the framework runs online on a microprocessor-class embedded target, **STM32F7 at 100 Hz control frequency** — this is the strongest evidence point for the deployment-feasibility question.

**Maturity.** Published, peer-reviewed (IEEE Transactions on Robotics, vol. 40, 2024, pp. 382–402), with real hardware (quadrotor) validation, not simulation-only.

### 2. K-ESKF (Koopman-Enhanced Error-State Kalman Filter)

**Mechanism.** Lifts the full nonlinear quadrotor state into a bilinear control system (linear-in-state, driven by measured accelerations and angular rates) via Koopman theory; a deep neural network parameterizes the Koopman observable (lifting) functions. The learned bilinear system replaces/extends the propagation (prediction) step of a standard error-state Kalman filter — i.e., this is a **state estimator**, not a disturbance estimator: it improves attitude/velocity propagation accuracy, which a Koopman disturbance-observer's residual computation would depend on.

**Evidence.** Trained/evaluated on the open NeuroBEM quadrotor dataset (real agile-flight telemetry, not purely simulated). Reported **60% lower attitude error versus a first-order Euler integration baseline** in propagation-model accuracy (multiple independent search snippets corroborate this exact figure).

**Maturity.** Peer-reviewed conference paper (IEEE/RSJ IROS 2024), evaluated on real flight data; no evidence in the accessible material of onboard/embedded real-time deployment (evaluated as an offline/desktop filter-accuracy study against a real dataset, not flown closed-loop).

### 3. Enhanced Koopman-DMD Data-Driven Control for 3-DOF AUV

**Mechanism.** Builds a linear data-driven AUV dynamics model via Koopman theory using Dynamic Mode Decomposition (DMD) on operational input-output data, then wraps it in a Fractional Sliding Mode Controller (FSMC) for robustness against hydrodynamic uncertainty (drag, buoyancy, added mass). This is a full model+control replacement, not a bolt-on observer module — the Koopman model IS the plant model the controller uses, so it does not compose cleanly with an existing separately-trained policy.

**Evidence.** Published in *Ocean Engineering*, Vol. 307, Article 118227 (2024). The accessible abstract states only that "efficacy... has been verified through simulation results" — **no real-vehicle test, no quantitative numbers in the retrievable abstract**.

**Maturity.** Simulation-only (per abstract); no field/real-AUV validation found.

### 4. OM-Koop — Online Memorable Koopman Operator Learning for Marine Robots

**Mechanism.** Constructs a Koopman-operator-based *uncertainty* (residual dynamics) model online, using the steering model's state error plus a sliding-window buffer; an LSTM is folded into the online Koopman-operator construction to give it memory across regimes. Critically, eigenvalues of the learned Koopman operator are constrained during online adaptation to preserve Lyapunov stability — this directly targets the "won't the online update destabilize the estimator" failure mode that a naive recursive Koopman update has.

**Evidence.** **Field experiments on real USVs and AUVs** (not simulation) — comparative results against other online-learning strategies show better adaptability/robustness while provably retaining stability. This is the closest existing precedent to "a Koopman-based online estimator running on a real marine vehicle."

**Maturity.** Peer-reviewed IEEE journal paper (2025/2026), field-validated on real marine hardware — the most mature/marine-specific of the set.

### 5. CR-RKL — Covariance-Regulated Recursive Koopman Learning (algorithmic core for "online/recursive EDMD")

**Mechanism.** This is the general recursive-least-squares formulation your "online/recursive EDMD" sub-bullet is pointing at. Standard recursive EDMD (Koopman operator estimated as RLS with exponential forgetting factor λ) is numerically unstable under persistent excitation loss — the covariance matrix P_k blows up. CR-RKL fixes this with two mechanisms: (a) error dead-zone gating — suspend covariance updates when prediction error is already small, and (b) constant-trace normalization — rescale P_k every step to hold trace(P_k) constant, bounding the adaptation gain while preserving its directional structure.

**Evidence, with numbers.** On a simulated differential-drive robot with wheel slip + Stribeck friction: vanilla online RLS diverges (‖P‖_F → 2.5×10⁴⁶), while dead-zone-gating holds error at 1.1×10⁻³ and constant-trace holds error at 5.6×10⁻³ — i.e., the regularization is not cosmetic, it is what keeps online Koopman estimation usable at all under realistic excitation. Also validated on real flight telemetry from a 26 g flapping-wing MAV (10-state attitude/velocity dynamics, 100 Hz) across cross-regime maneuvers, though no closed-loop hardware control was demonstrated there.

**Maturity.** arXiv preprint only (2606.15317, 2026), not marine, not yet closed-loop on physical hardware for the MAV case — but this is the piece your "recursive EDMD" ask decomposes into, and it exposes a concrete failure mode (covariance divergence) any from-scratch online Koopman observer on your UUV would need to guard against.

---

## Applicability to Our Stack

**Where it would plug in.** A lightweight Koopman disturbance/current observer running on the real UUV would sit purely at deployment time, upstream of the GRU student — producing a low-dimensional disturbance/current estimate appended as an extra observation channel, composing with the existing obs4 IMU/pressure extra-obs channel at the same ZOH-2, ≤25 Hz bus rate. It would not touch the privileged encoder (p_t → z) or its training-time loss, so it does not reopen the "no auxiliary losses on the encoder" constraint — it is an entirely separate, deploy-side module.

**Compute.** EVOLVER's real-world demonstration point — full online Koopman-lift disturbance estimation on an STM32F7 microcontroller at 100 Hz — comfortably brackets our 25 Hz bus rate from above; OM-Koop's real-AUV/USV field deployment is independent corroboration that an online Koopman estimator is embedded-hardware-feasible on an actual underwater platform. Compute is not the blocker here. Numerical stability of the online update (CR-RKL's finding) is a real, concrete risk if we roll our own recursive estimator rather than reusing OM-Koop's eigenvalue-constrained formulation.

**Blockers.**
1. **No paper closes the exact loop we need.** None of the five demonstrate "Koopman observer output → extra input channel → distillation-trained downstream policy (GRU/DAgger)." OM-Koop feeds a steering *controller*, EVOLVER feeds feedforward compensation, K-ESKF feeds a state estimator — none feed a frozen/distilling learned policy's observation vector.
2. **Train/deploy consistency.** If the observer's output becomes a new student-obs channel, the teacher rollouts used for DAgger distillation would need this channel simulated consistently during training data collection (analogous to how obs4's IMU/pressure channels were added), or the student sees a channel at deploy time it never saw in distillation — this is unproven integration work, not something any of these papers address.
3. **Fault-regime coverage untested.** All five papers validate under smooth parameter drift or disturbance (current, wind, wheel slip); none validate under discrete regime shifts like our thruster-fault DR — a linear Koopman lift's dictionary may not span a fault-induced dynamics change, and this would need to be checked specifically under our fault DR sweep, not assumed from these results.
4. Our own board's compute budget for this workload is not established in the provided context — the EVOLVER/OM-Koop hardware precedents are evidence of feasibility elsewhere, not a verified number for our platform.

**Verdict: STRETCH** — hardware/compute feasibility is well-evidenced by EVOLVER (STM32F7 @ 100 Hz) and OM-Koop's real marine-vehicle field deployment, but the specific integration this category asks for (observer output as an extra GRU-student obs channel, DAgger-consistent, validated under our fault-DR regimes) has no direct precedent in any of these papers and would be new integration + validation work, not a drop-in adoption.

## Sources

- [EVOLVER project page](https://sites.google.com/view/buaa-evolver)
- [EVOLVER — IEEE T-RO 2024 abstract (ADS)](https://ui.adsabs.harvard.edu/abs/2024ITRob..40..382J/abstract)
- [K-ESKF — IEEE Xplore (IROS 2024)](https://ieeexplore.ieee.org/document/10802457/)
- [K-ESKF — full PDF](https://vodafone-chair.org/pbls/ketong-zheng/Data-Driven_Koopman_Operator-Based_Error-State_Kalman_Filter_for_Enhanced_State_Estimation_of_Quadrotors_in_Agile_Flight.pdf)
- [Enhanced Koopman operator-based robust data-driven control for 3-DOF AUV — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0029801824015658)
- [Enhanced Koopman operator-based robust data-driven control for 3-DOF AUV — ASU Elsevier Pure](https://asu.elsevierpure.com/en/publications/enhanced-koopman-operator-based-robust-data-driven-control-for-3-/)
- [OM-Koop — IEEE Xplore](https://ieeexplore.ieee.org/abstract/document/11123429)
- [OM-Koop — ResearchGate](https://www.researchgate.net/publication/394462264_OM-Koop_Online_Memorable_Koopman_Operator_Learning_for_Marine_Robots_Steering_Dynamics)
- [CR-RKL — arXiv:2606.15317](https://arxiv.org/abs/2606.15317)