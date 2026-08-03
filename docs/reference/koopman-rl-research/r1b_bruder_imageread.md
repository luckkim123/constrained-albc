# Bruder, Bombara, Wood — "A Koopman-based Residual Modeling Approach for the Control of a Soft Robot Arm"

IJRR 2025 (published version), DOI 10.1177/02783649241272114. Extracted from PDF downloaded at
`https://ntrs.nasa.gov/api/citations/20250001907/downloads/ResidualKoopmanModel_IJRR.pdf` via the
page-image route (pdftoppm -r 150, 17 pages, all read with the Read tool — text layer was not used).
All 17 pages were read in full (title through references); no supplementary/appendix volume beyond
page 17 exists in this PDF.

---

## a. The exact recipe

**Physics prior**: an *idealized analytical nonlinear ODE model*, not a numerical simulator.
- Van der Pol oscillator (Eq. 28): known closed-form ODE, with an intentionally wrong damping
  coefficient assumed (µ=0.72 assumed vs. true µ values drawn from [0,1], e.g. µ=0.04 in Fig. 3).
- Pendulum-on-cart (Eq. 34): known closed-form ODE with deliberately mis-specified mass/damping
  parameters (assumed m=0.9, M=1.1, c_d=1 vs. true m=1, M=1, c_d=0.2).
- Real soft arm: an Euler-Lagrange model (p.9, p.14) derived under a discretized piecewise-constant-curvature
  assumption, with heuristically-chosen link masses/joint stiffnesses/damping (not fit to the real
  arm's true parameters) — the paper itself calls this "physics-based nonlinear dynamical model" (§3.3.1).

Critically, the physics prior is turned into a Koopman matrix **analytically/algebraically**, not by
running rollouts: the method (adapted from Asada 2023, cited p.4) computes the Koopman generator matrix
K̄_p by projecting each basis function's time-derivative (via the chain rule, Eq. 21) onto the chosen
basis set using inner-product projections (Eq. 19, 20), then exponentiates the generator: K̄_p = e^{τ Ḡ_p}
(Eq. 23). For low-dimensional systems (Van der Pol) the inner products are computed by direct/exact
integration; for higher-dimensional systems (pendulum-cart, real arm) they are approximated via Monte
Carlo integration (§2.4.1, p.6-7: 1000 samples over [-10,10]^3 for the pendulum-cart). **No trajectory
simulation of the physics model is performed at all** — this is a direct operator-projection method, not
"pretrain on simulator rollouts."

**Residual operator**: identified via batch EDMD (Extended Dynamic Mode Decomposition) least-squares
regression on real-system snapshot pairs (Eq. 25-26): K̄_e = argmin Σ ‖K̄ᵀp^(k) − q^(k)‖². The residual
matrix is then simply the *difference* K̄_r := K̄_e − K̄_p (p.5, Eq. following 26) — i.e. "residual" means
literally "empirical-minus-physics" in the Koopman-matrix space, not a separately-parameterized residual
model architecture.

**How combined**: additive **in the lifted (Koopman-matrix) space**, not in raw state space:
> "ψ_{k+1} = (K̄_p^T + γK̄_r^T) ψ_k,  x_k = Cψ_k" (Eq. 13, p.4; restated as Eq. 32/36 per-system)

A scalar weighting factor γ ∈ [0,1] (found by a second least-squares fit on a held-out snapshot split
S_2, Eq. 27, p.5) interpolates between pure-physics (γ=0) and pure-data (γ=1): "As the amount of training
data increases, γ will tend toward 1, but when limited data is available it will remain closer to 0,
placing more confidence in the physics-based model" (p.5). Lasso regularization (λ tuned manually,
non-zero only for the real-arm case: λ=2.95e-2 for K̄_r, λ=5e-5 for the purely data-driven K̄_d) is
applied to prevent overfitting (§2.4.2, p.8-9).

The whole pipeline is summarized as Algorithm 1 (p.6).

---

## b. The "<10% of the data" claim

**NOT FOUND as worded.** This exact phrase/number does not appear anywhere in the paper — not in the
abstract (verbatim abstract text, p.1: "...require less data to construct than purely data-driven models...
[the arm can] track end-effector trajectories, perform a pick-and-place task, and write on a dry-erase
board..." — no percentage given), not in the Discussion, not in the Conclusion. I read the full abstract,
Discussion (§5, p.12-14) and Conclusion (§6, p.13) and grepped visually for any "10%"/"data efficiency"
statement; none exists in this published IJRR version. **The task brief's characterization of the
abstract may be describing a different document (e.g., a conference/workshop version, or a
paraphrase/hallucination) — it does not match this PDF.**

What the paper *does* report quantitatively (Discussion §5, p.12):
- Van der Pol (simulated): combined model gives an **8% RMSE reduction vs. physics-based**, **28%
  reduction vs. data-driven** (aggregated over all 9 µ values × 9 dataset sizes).
- Pendulum-on-cart (simulated): **5% reduction vs. physics-based**, **18% reduction vs. data-driven**.
- Real soft arm: **52% reduction vs. physics-based**, **68% reduction vs. data-driven** (Experiment 1
  prediction accuracy, both Ramp-2s/Ramp-4s trials, Table 1).

**Is there an actual sample-efficiency CURVE?** Yes, but only for the two **simulated** systems, and it
plots error vs. *snapshot count*, not a "vs. % of a benchmark's data" framing:
- **Figure 4** (p.10): x-axis = "Training Data Snapshots" (300 to 1100, in steps of 100), y-axis = RMSE
  (0.2–1.0). Three curves: Physics-based (flat, ~0.35, independent of data since it uses none), Data-driven
  (starts ~0.95 at 300 snapshots, decreases monotonically-ish to ~0.22 by 1100), Combined (starts ~0.4,
  settles near the physics-based line ~0.3–0.35 across the whole range, dips at times below both).
  Caption: "The combined model error is comparable to the physics-based model when data is scarce, and
  comparable to the data-driven model when data is abundant." Discussion text (p.12) states explicitly:
  data-driven RMSE "dropped from 0.94 to 0.22" going from 300→1100 snapshots, and concludes "the combined
  model achieves similar accuracy with much less data" — but gives no single ratio like "<10%".
- **Figure 5** (p.10): same style for pendulum-on-cart, x-axis 200–2000 snapshots. Combined model curve is
  flatter/more consistent than the data-driven curve (caption: "not always the smallest, but more consistent").

**On the real hardware, there is NO such sweep** — a single fixed dataset (K=30000 snapshots from ten
120s trials, §3.3.2 p.9) was used to build both the residual and the purely-data-driven real-arm models;
the paper never varies the amount of *real* training data and re-measures error. So a genuine
real-hardware "error vs. amount of real data" curve does **not exist** in this paper — confirming the
research-doc's second claim (see Verdict below), but for a different, more specific reason than "no
curve at all": the curve exists for simulated toy systems, not for the physical arm.

---

## c. Recursive / online update mechanism

**NOT FOUND — does not exist in this paper.** All model identification (physics-based projection,
empirical EDMD, γ selection) is explicitly **offline / batch**: least-squares over a fixed, pre-collected
snapshot set (Eq. 26, 27), computed once before deployment. The paper is explicit that this is a
limitation, not a feature, listing it as unaddressed future work in the Conclusion (§6, p.13):

> "Further work should investigate adapting our modeling approach to an online learning context. **While
> in this work all models were identified offline**, the computational efficiency of constructing
> data-driven Koopman models and the reduced data requirements of our approach make it well suited for
> online model refinement."

No RLS (recursive least squares), no online/incremental EDMD update, and no stability safeguards for a
recursive update are described or evaluated anywhere in the method (§2), the three systems (§3), the
three experiments (§4), or the discussion (§5) — "well suited for online model refinement" is a forward-looking
claim about feasibility, not a demonstrated mechanism. This directly contradicts the brief's characterization
of the abstract mentioning "real-time recursive Koopman model updates" — no such statement or mechanism
is present in this paper.

---

## d. Hardware validation scope

**Robot** (Fig. 2, p.8): a real pneumatically-actuated soft arm with three bending segments in series,
each with a compliant-hinge spine flanked by two co-contracting McKibben artificial muscles (6 actuators
total, pressure-controlled 0–207 kPa); consecutive segments offset 90° so bending planes are orthogonal
(enabling 3D end-effector motion from a per-segment 2D-bending mechanism). End effector = vacuum-driven
origami gripper (Li et al. 2019 style). Sensing = Vicon motion-capture of segment-end markers, converted
to joint angles via nonlinear-optimization inverse kinematics (Appendix, Eq. 47-49, p.15).

**Tasks and results**:
1. **Prediction accuracy** (§4.1, real arm): two 120s validation trials (2s-interpolated and 4s-interpolated
   random pressure waypoints). RMSE (Table 1, mm): Physics-based 139/143mm, Data-driven 208/222mm,
   Combined **71/65mm**. Text (p.10) states aggregate RMSE = 0.14m physics, 0.21m data-driven, **0.07m combined**.
2. **Controller performance / trajectory tracking** (§4.2, K-MPC): circle (30s) and figure-eight (60s)
   end-effector trajectories (Figs. 7-8). Table 1: Circle RMSE 167mm (physics) / 684mm (data-driven) /
   **67mm (combined)**; Figure-eight 192mm / 684mm / **73mm**. The data-driven controller's optimal control
   input was always zero — "unable to move the arm from the origin" (p.13) — a total failure, not merely
   worse tracking. Physics-based MPC RMSE was "more than 2.5 times larger" than combined (p.13).
3. **Pick-and-place** (§4.3.1, Fig. 9): combined-model K-MPC moved the arm to a fixed "pick" position where
   a human hands it an object, then dropped it in one of two bins 9.5cm apart. 5 items (2 screwdrivers, 1
   tape roll, 2 paper balls), sequence pre-programmed (no perception/sorting logic); all items placed
   correctly, including recovery when a screwdriver snagged on the robot's base.
4. **Writing demonstration** (§4.3.2, Fig. 10): drew a stylized letter "H" on a dry-erase board using a
   predefined 3D end-effector trajectory (curved because the arm's reachable workspace couldn't realize a
   planar path); relied on body compliance against the board's planar constraint. 3 trials, board pose
   changed slightly each time (no controller re-tuning); succeeded in all 3.

---

## e. Simulator vs. analytical physics prior

**Analytical physics model, not a simulator.** As detailed in (a): the "physics-based" Koopman component
K̄_p is built by projecting a closed-form ODE's vector field directly into the chosen (Hermite-polynomial)
basis via inner-product computation (exact integration for 2D systems, Monte Carlo integration of the
projection integrals for higher-dimensional systems) and then matrix-exponentiating the resulting
generator. This is a **one-shot analytic/algebraic operation on the equations of motion** — at no point
does the method roll out trajectories through a numerical ODE solver or a physics engine to generate the
physics-based Koopman matrix. (ODE solving/Matlab `ode45` is used elsewhere in the paper, but only to
*generate synthetic "real" training/validation data* for the two simulated benchmark systems — Van der
Pol and pendulum-cart — standing in for what would be real sensor data; it is never used to build K̄_p.)

**Implication for the mapping to a sim-Koopman + real-residual recipe**: this paper's recipe is "known
governing equations (an idealized analytical model, possibly with wrong parameters) → algebraic Koopman
projection" plus "EDMD residual fit on real data" — i.e., an **analytic-prior + data-residual** recipe.
It does **not** demonstrate or map onto a "train/pretrain a Koopman (or neural) model against a full
numerical simulator (e.g., Isaac Sim rollouts), then EDMD-refit a residual against real hardware data"
recipe, because no simulator of that kind appears anywhere in this paper. For a UUV/ALBC context where the
"sim" side would be a GPU physics simulator, this paper is a template only for the *general
additive-in-lifted-space, EDMD-residual, offline* mechanics — not for the specific "simulator pretraining"
step, which this paper never performs (its physics prior is a hand-derived equation, not a simulator).

---

## f. Transfer / generalization / regime-change robustness

**Only anecdotal, not a designed generalization study.** No formal experiment varies payload mass,
actuator wear, or environmental conditions and measures model/controller degradation. The closest evidence:
- Writing task (§4.3.2): board position/orientation was "changed slightly before each trial to assess the
  robot's ability to accommodate disturbances without modifying its controller" (p.11) — 3 trials, all
  succeeded, but this is a small, qualitative, undocumented-magnitude perturbation, and the response
  attributed to *body compliance*, not model/controller adaptation.
- Pick-and-place (§4.3.1): handled 5 different physical objects (2 screwdrivers, 1 tape roll, 2 crumpled
  paper balls) of presumably different (unspecified, unmeasured) mass/shape without incident, plus
  recovered from an unplanned obstruction (screwdriver snagging the base) — again attributed to compliance,
  not evidence of model robustness to a parameter/payload regime shift.
- No cross-configuration/cross-payload retraining or evaluation of model prediction error under an
  intentionally shifted regime (e.g., "trained without payload, tested with a known added mass") is present.

**Verdict for (f): NOT FOUND** — the paper offers no controlled generalization/regime-change experiment;
robustness claims in §4.3 are task-success anecdotes attributed primarily to the soft arm's physical
compliance rather than to the Koopman model's generalization properties.

---

## Summary of key figures encountered

| Figure | Content | Axes/format |
|---|---|---|
| Fig. 1 (p.8) | Pendulum-on-cart schematic | diagram |
| Fig. 2 (p.8) | Real soft-arm hardware photo, annotated (McKibben muscles, hinge joints, motion-capture markers, pressure regulators, origami gripper) | photo |
| Fig. 3 (p.10) | Van der Pol phase portrait: real vs. physics-based vs. data-driven vs. combined model trajectories, one trial | x1 vs x2 phase plane |
| **Fig. 4 (p.10)** | **Van der Pol sample-efficiency curve**: RMSE vs. training-data snapshot count (300–1100), 3 curves (physics-based flat, data-driven decreasing, combined flat-ish near physics level) | RMSE vs snapshots |
| **Fig. 5 (p.10)** | **Pendulum-on-cart sample-efficiency curve**, same style, 200–2000 snapshots | RMSE vs snapshots |
| Fig. 6 (p.11) | Real-arm model predictions (x/y/z position + prediction error over time) for the two validation trials, 3 models overlaid | time series |
| Fig. 7 (p.11) | Circle-trajectory K-MPC tracking (3D + per-axis time series + tracking error), 3 controllers | time series + 3D |
| Fig. 8 (p.11) | Figure-eight-trajectory K-MPC tracking, same format | time series + 3D |
| Fig. 9 (p.12) | Pick-and-place demonstration photos | photo |
| Fig. 10 (p.12) | Writing-on-whiteboard demonstration photo | photo |
| Fig. 11 (p.14) | Robot arm kinematics diagram (link/joint frames) | diagram |
| Table 1 (p.12) | RMSE/variance (mm) for all 3 models × 4 trial types (Ramp2s, Ramp4s, Circle, Eight) | table |

No data-efficiency curve exists for the real hardware system — Figs. 4-5 (the only sample-efficiency
curves in the paper) are both on simulated benchmark systems (Van der Pol, pendulum-on-cart), not the
soft arm.
