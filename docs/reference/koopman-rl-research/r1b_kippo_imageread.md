# KIPPO (arXiv:2505.14566) — Image-Route Extraction Findings

Source: `kippo.pdf` (arXiv v1, 20 May 2025, 22 pages) downloaded from `https://arxiv.org/pdf/2505.14566`,
rendered to PNG at 150 DPI (page 19 also re-rendered at 400 DPI) via `pdftoppm`, read visually page-by-page.
Text layer confirmed unusable (`pdftotext` returns FlateDecode binary garbage per prior agents); this route
worked — all pages rendered and read cleanly. Pages stored at
`/root/.claude/jobs/add36792/tmp/kippo_pages/page-01.png` … `page-22.png` (not deleted).

---

## a. φ_x / Koopman-module update schedule vs PPO

**Official paper — Algorithm 3 "Optimization Phase" (page 19):**

- KIPPO uses **one joint loss** and **one combined gradient step**, not an alternating/separate schedule.
  Per mini-batch, within the *same* epoch loop used for PPO:
  1. Compute `L_pred-ls`, `L_pred-ss` (via `LatentSpacePrediction`, Algorithm 2) and `L_rec` (line 16).
  2. `L_KI ← ω1·L_rec + ω2·L_pred-ls + ω3·L_pred-ss` (line 17).
  3. `L_PPO ← ComputePPOLoss({φ_x^sg(x), u, ...}_B)` (line 18) — **`φ_x(x)` is stop-gradiented before
     being fed into the PPO loss** (see below).
  4. `L_KIPPO ← L_KI + L_PPO` (line 19, "Total loss").
  5. "Compute gradients of `L_KIPPO` with respect to model parameters" (line 20) → single `.backward()`.
  6. "Update model parameters with gradient descent" (line 21) → single optimizer step.
  - This repeats for `N_epochs = 10` epochs over 32 minibatches (2,048 rollout steps split into 32
    minibatches), every rollout-optimization cycle, for the full 1M environment steps. **No separate
    schedule where the Koopman module updates less/more often than PPO** — they update together, every
    minibatch, every epoch.

- **Stop-gradient confirmed.** Algorithm 3 line 18 renders `φ_x` with a superscript glyph that displays as a
  garbled/undefined character (likely an unrendered custom LaTeX macro, possibly `\text{sg}[\cdot]` or a
  slashed-∇ symbol — the PDF's embedded font does not render it as normal text). Its **meaning is spelled out
  explicitly in prose**, Appendix F.3 (page 13, "Optimization Process"):

  > "The collected data is divided into mini-batches. For each mini-batch, the algorithm computes the
  > reconstruction loss, latent-space prediction loss, state-space prediction loss, and the PPO loss,
  > L_PPO. The actor and critic networks operate on the encoded states, enabling learning in the simplified
  > latent space. **The [garbled-glyph] operator ensures the state representations are optimized
  > independently of the PPO loss.**"

  Combined with Section 4.1 (page 7): "A key feature is the **complete decoupling of representation
  learning from policy optimization**. The representation learning components optimize independently from
  policy and value networks. This separation ensures improvements stem from the learned representation."

  → **Policy/value gradients do NOT flow into φ_x, φ_x⁻¹, φ_u, K, or B.** Those five components receive
  gradients only from `L_KI` (i.e., `L_rec`, `L_pred-ls`, `L_pred-ss`). The actor/critic receive gradients
  only from `L_PPO`, using `φ_x(x)` as a (stop-gradiented) fixed input. The single combined backward pass
  (`L_KIPPO = L_KI + L_PPO`) is safe precisely because of this stop-gradient — it is mathematically
  equivalent to two separate backward passes over disjoint parameter sets.

- **Separate optimizer? NO — single shared optimizer, single LR**, per Table B.1 (page 11, "Shared
  hyperparameters for the baseline PPO models and KIPPO"): **Optimizer = Adam, Learning Rate α = 3×10⁻⁴, LR
  Annealing = Yes, Max Gradient Norm = 0.5.** Table B.1's title explicitly states this configuration is
  *shared* between PPO baseline and KIPPO. Page 6 text: "Both components update their parameters using the
  Adam optimizer." No separate LR is given anywhere for the representation-learning components.

- Also confirmed by Algorithm 1 "Rollouts Phase" (page 18): during rollout, `y_t ← φ_x(x_t)` is computed
  fresh every step to drive the policy (`u_t ~ π_θ(·|y_t)`) and value (`V_t ← V^π_θ(y_t)`) — i.e., φ_x runs
  in inference mode during rollout (implicitly no gradient, consistent with standard on-policy rollout
  collection), and only the *Optimization Phase* (Algorithm 3) computes gradients.

## b. Loss definitions and weights

Section 3.3 "Loss Formulation" (page 5), equations 2–6:

- **Reconstruction loss** (Eq. 2): `L_rec(t) = { φ_x⁻¹(φ_x(x_t)) − x_t }²`. Targets "informativeness."
  Note: action reconstruction loss is explicitly *omitted* ("the sole purpose of the action encoder is to
  influence state transitions in the latent space, and the accuracy of action encoding is implicitly
  enforced through future state prediction losses. Empirical studies also confirm that including action
  reconstruction terms does not yield significant performance improvements.")

- **Latent-space prediction loss** (Eq. 3): `L_pred-ls(t) = (1/H) Σ_{h=1}^{H} m_{t,h} (ŷ_{t+h} − φ_x(x_{t+h}))²`.
  Targets "simplification" and "predictability" in latent space.

- **Binary episode mask** (Eq. 4): `m_{t,h} = 1` if trajectory not ended by step `(t+h−1)`, else `0`.

- **State-space prediction loss** (Eq. 5): `L_pred-ss(t) = (1/H) Σ_{h=1}^{H} m_{t,h} (φ_x⁻¹(ŷ_{t+h}) − x_{t+h})²`.
  Targets "consistency"/"predictability" in the original state space; "prevents the latent space from
  diverging too far from physically meaningful representations."

- **Total representation loss** (Eq. 6): `L_KI = (1/T) Σ_{t=0}^{T} (ω1·L_rec(t) + ω2·L_pred-ls(t) + ω3·L_pred-ss(t))`.

- **Total framework loss** (Eq. 7, page 6): `L_KIPPO = L_KI + L_PPO`.

- **Default weights used in the main experiments (Table 2 results)** — Table B.2 (page 11):
  `ω1 (L_rec) = 0.75`, `ω2 (L_pred-ls) = 0.1`, `ω3 (L_pred-ss) = 0.5`. Number of layers = 2, neurons/layer = 128
  (fixed; only latent dim and horizon H were varied per-environment).

- **Horizon H**: two different statements in the paper —
  - Main text (Section 3.2, page 4): "Empirically, horizons of 8-32 steps are effective, with longer
    horizons benefiting environments with significant temporal dependencies or sparse rewards."
  - But the actual **swept/reported range in Appendix E.1–E.3 and Table B.2 is only H ∈ {1, 3, 5, 10}**
    (Table E.1, page 20: "Prediction Horizon: 1, 3, 5, 10"). **This is an internal inconsistency in the
    paper** — the "8–32 steps effective" claim is not supported by any table actually shown; the swept
    values never reach 8+.
  - Per-environment best H (Table E.3, page 22): InvertedPendulum H=3 best (998.18), Hopper H=3 best
    (2520.53), Walker2d H=1 best (3325.74), HalfCheetah H=10 best (3089.20), LunarLander H=5 best (280.81),
    BipedalWalker H=3 best (255.91) — i.e., optimal H is environment-specific and never exceeds 10 in the
    actual sweep.

- Loss weights were also swept 0.00–1.00 in increments of 0.05 (Appendix E.3, Table E.1) for sensitivity
  analysis (Figs. E.3–E.5, pages 15).

## c. Latent dimension per environment / "2-4× state dimension" guidance

**Exact quote**, Section 3.1 "Architecture Design" (page 3, right column):

> "The dimensions of the state-transition matrix **K** and control matrix **B** correspond to the chosen
> latent space dimensionality. **This is typically set to 2-4 times the state dimension**, providing
> sufficient capacity to capture complex dynamics without excessive computational overhead."

Actual swept per-environment latent dims (Table E.1, page 20 / Table E.2, page 21): {16, 32, 48} were the
values explored across all six environments (Table B.2, page 11, lists "Varied (16, 32, 48)" as the main
sweep, though Figure E.1 (page 14) shows a fourth value, 64, was also tested in the extended hyperparameter
analysis of 300 configs/7,200 models). Given state dims |S| ∈ {4, 8, 11, 17, 17, 24} (Table 1, page 8), the
"2-4×" guidance would suggest per-env dims like 8–16 (Pendulum), 16–32 (LunarLander), 22–44 (Hopper),
34–68 (Walker2d/HalfCheetah), 48–96 (BipedalWalker) — but no table gives one single "final chosen" per-env
dimension; the paper instead reports sweep results across the *same* shared grid {16,32,48(,64)} for every
environment (best value differs per environment, e.g. HalfCheetah keeps improving to 48, InvertedPendulum
plateaus after 32 — Table E.2, page 21).

## d. Variance-reduction claim "26.89-91.43%" — verbatim sentence + exception

**Exact quote**, Section 4.2 "Comparison with Baselines" (page 7, left column):

> "KIPPO also shows lower SD in most environments, demonstrating enhanced consistency across seeds,
> **reducing variance by 26.89-91.43% versus PPO (one exception) and 58.94-90.21% versus RPO (two
> exceptions)**. We will further discuss the exceptional cases in the ablation study."

**Exception environment (vs. PPO): HalfCheetah-v4.** Confirmed via Figure 1 (page 2, right panel, "Std.
Final Returns / KIPPO % Diff."): the only positive (variance-*increasing*) bar is HalfCheetah at **+16.76%**;
all others are negative (variance-reducing): InvertedPendulum −91.43%, Hopper −55.76%, Walker2d −36.08%,
LunarLander −28.66%, BipedalWalker −26.89%. So the quoted range 26.89–91.43% is exactly the min/max of the
five *negative* (improving) environments, excluding HalfCheetah's +16.76% outlier — this is stated
explicitly to be discussed further in the ablation study (Section 4.3/Appendix D), where Table 2 (page 9)
independently confirms HalfCheetah KIPPO std = 1203.42 vs. PPO baseline std = 1030.66 (an increase).

The paper does not, in the pages read, give the analogous "one exception" / "two exceptions" identity for
RPO explicitly by name (only the PPO exception is pinned down via Figure 1's per-env bar values); the RPO
comparison exceptions were not individually labeled in the text I could locate.

## e. Seeds/trials protocol and compute note

- **4 random seeds per environment**, Section 4.1 "Training Configuration" (page 8):
  > "Each experiment uses 4 random initialization seeds (1, 2, 3, 4) per environment. We selected 4 seeds as
  > a balance between the original PPO paper's 3 seeds [Schulman et al., 2017b] and CleanRL's standard 5
  > seeds... Each training run consists of exactly 1 million environment steps."
- **6 environments × 4 seeds = 24 runs** for the main comparison, confirmed twice:
  - Section 4.4 (page 7): "Training KIPPO takes approximately 15% longer than PPO (15 hours vs. 13 hours for
    **24 parallel models**)..."
  - Appendix B.3 "Hardware and Runtime Details" (page 10): "We conducted experiments in parallel across
    **four seeds and six environments, totaling 24 simultaneous training runs**. Each experiment used a
    dedicated core of an Intel Xeon Gold 6248R CPU (3.00GHz, 24 cores per socket, 2 sockets). The system used
    a single NVIDIA Tesla V100S-PCIe-32GB GPU for one complete set of 24 runs. This configuration required
    approximately 15 hours for KIPPO and 13 hours for baseline PPO, demonstrating practical applicability
    with modest computational overhead."
- Results reported as mean ± std across these 4 trials (e.g. Table 2 caption, page 9: "across four trials";
  Fig. 1 caption, page 2: "across four trials per environment"). At inference time, only the encoder is used
  ("this computational overhead exists only during training; at inference time, only the encoder is used
  with negligible additional computational cost," page 7).
- Separately, the hyperparameter-sensitivity study (Appendix E, page 12) is much larger: "**we trained 300
  model configurations, each with 4 random seeds across 6 environments, resulting in 7,200 trained models**."

## f. Section 3.1 rejection of raw-state concatenation (Draeger et al. 1995)

**Not in Section 3.1** as guessed in the task brief — the actual passage is in **Appendix G, "Latent Space
Properties"** (page 13, right column), immediately after Eq. 11:

> "Because some systems require a higher dimension to represent non-linear dynamics linearly, we encode to a
> space in a higher dimension than the state and action space. **Unlike [Song et al., 2021], we do not
> concatenate the original state with the encoded state, as this restricts the set of systems where
> linearization is possible. Specifically, finding a linear representation of a non-linear system that
> includes the original state becomes impossible when the system has multiple fixed points or general
> attractors. This limitation arises because linear systems (with a single fixed point at the origin) are
> not topologically conjugate to non-linear systems with multiple fixed points [Draeger et al., 1995].**"

Preceding context (Eq. 10–11, same page) gives the worked toy example motivating the higher-dimensional
lift: a nonlinear system `dx1/dt = x1²`, `dx2/dt = x1x2 + x2` is linearized via `[y1,y2,y3] = [x1², x2, x1x2]`
— 2 state dims → 3 latent dims, illustrating why the latent space must sometimes exceed the state dimension.
`[Draeger et al., 1995]` in the References (page 9) is: "A. Draeger, S. Engell, and H. Ranke. Model predictive
control using neural networks. *IEEE Control Systems Magazine*, 15(5):61–66, Oct 1995."

## g. Actor/critic input: y_t only, or [x_t, φ_x(x_t)]?

**Both actor and critic consume ONLY the encoded state `y_t = φ_x(x_t)` — never the raw state, and never a
concatenation of the two.**

- Figure 2 caption (page 3): "The policy optimization algorithm operates on the encoded states `y_t =
  φ_x(x_t)`."
- Algorithm 1 "Rollouts Phase" (page 18), lines 7–10:
  ```
  y_t ← φ_x(x_t)              ▷ Encode the current state to obtain the latent representation
  u_t ~ π_θ(·|y_t)             ▷ Sample an action from the policy
  log π_t ← log π_θ(u_t|y_t)   ▷ Compute the action's log probability
  V_t ← V^π_θ(y_t)             ▷ Estimate the latent state value
  ```
  — both the actor (`π_θ`) and critic (`V^π_θ`) are called with `y_t` as the sole argument.
- Appendix F.3 (page 13): "The actor and critic networks operate on the encoded states, enabling learning in
  the simplified latent space."
- Design principle (page 6, contribution #2): "KIPPO adds an auxiliary network to policy gradient baselines
  like PPO **without altering the core policy or value function architecture**. This design allows the
  policy to train on a simpler, encoded state space while the auxiliary network enforces a linear-like
  structure." This is architecturally consistent with y_t-only input (concatenation would require resizing
  the policy/value input layer, which the paper explicitly says it avoids).

## h. When is φ_x frozen? / Input normalization before φ_x?

- **Never frozen; trained continuously end-to-end throughout all 1M steps**, alongside the policy, in every
  optimization phase (Algorithm 3 runs every rollout-optimization cycle, all the way to "1 million
  environment steps," page 6). No pretraining phase, no freeze-after-N-steps schedule, and no mention of
  freezing φ_x at any point in the 22 pages read. "The latent representation is learned incrementally
  throughout training, with parameters adapting gradually across rollout-optimization cycles... preventing
  disruptive changes that could destabilize learning" (page 6) — i.e. it keeps training the whole run, just
  with (implicitly) small/stable updates due to the joint schedule, not because it's frozen.
- **Input normalization: NOT FOUND.** No sentence in Sections 2, 3, 4, or Appendices A/B/F/G states that `x`
  is normalized (e.g., running mean/std, min-max, or clipping) before being passed to `φ_x`. The official
  paper's Algorithm 1/3 pseudocode shows `φ_x(x_t)` applied directly to the raw environment observation with
  no normalization step in the math or the prose. (Contrast with the **unofficial reimplementation**, which
  *does* add observation clipping — see below — a detail absent from the official paper.)

---

## Secondary: UNOFFICIAL PyTorch reimplementation (Bluehorse-hub/KIPPO-PyTorch-Unofficial)

Cloned successfully (shallow, depth 1) to
`/root/.claude/jobs/add36792/tmp/kippo_pages/KIPPO-PyTorch-Unofficial/`. **Everything below is from this
UNOFFICIAL, community reimplementation — not the paper authors' code** (README explicitly disclaims: "the
original authors have not released their official implementation... independently developed based on the
algorithmic descriptions in the paper," "not affiliated with or endorsed by the original authors"). It only
implements a single environment (`HalfCheetah-v5`), not all six.

Regarding question (a), the training loop (`train.py`, `models/Koopman/Koopman.py`,
`models/Agent/PPO.py`):

- **UNOFFICIAL REIMPLEMENTATION diverges structurally from the paper's Algorithm 3**: instead of one joint
  `L_KIPPO = L_KI + L_PPO` loss and one combined backward pass, this code uses **two fully separate `Adam`
  optimizers** and **two separate, sequential `.train()` calls per update** (`koopman.train()` then
  `agent.train()` in `train.py` lines 146–147):
  - `Koopman.optimizer = Adam(phi_x + phi_x_inv + phi_u + B + K params, lr=3e-4)` (`Koopman.py` line 16–18),
    runs its own inner loop over `args.epochs` (default 10) with its own `.backward()`/`.step()` per batch
    (line 57–59): `loss_ki = 0.75*loss_rec + 0.1*loss_predls + 0.5*loss_predss` — **the loss weights exactly
    match the paper's Table B.2 defaults** (ω1=0.75, ω2=0.1, ω3=0.5).
  - `PPO.optimizer = Adam(actor + critic params, lr=args.agent_lr=3e-4)` (`PPO.py` line 32), its own separate
    loop over `args.epochs` (10), with gradient clipping `max_norm=0.5` (matches paper Table B.1) and a
    linear LR annealing schedule (`linear_lr_scheduler`, matches paper's "LR Annealing: Yes").
  - Because the two optimizers own **disjoint parameter sets** (Koopman optimizer never touches
    actor/critic, PPO optimizer never touches phi_x/phi_x_inv/phi_u/B/K), and because the rollout phase
    computes `latent_state = phi_x(state)` under `torch.no_grad()` (`train.py` line 115–118) before storing
    it in the replay buffer, this achieves the **same practical effect as the paper's stop-gradient** (actor
    loss cannot backprop into φ_x) — but via disjoint optimizers + no-grad-collected buffer states, not via
    an explicit detach in a combined loss. **Update schedule is thus sequential per iteration (Koopman full
    10-epoch pass, then PPO full 10-epoch pass), not interleaved as one joint per-minibatch step** as
    Algorithm 3's pseudocode literally shows.
  - **Deviation**: the Koopman optimizer has no LR annealing and no gradient clipping applied (unlike PPO's),
    even though the paper's Table B.1 lists LR Annealing and Max Gradient Norm as "shared" hyperparameters
    for "the baseline PPO models and KIPPO."
  - **Deviation/addition not in the paper**: `train.py` line 113 / `PPO.py` line 138 add explicit
    **observation clipping** (`state = torch.clamp(state, -10.0, 10.0)`) before `phi_x(state)` — this is a
    form of input normalization the official paper's text never mentions (see item h above).
  - Both actor and critic consume only the latent state (`latent_state`/`batch_states` post-`phi_x`), never
    raw state — consistent with the official paper (item g).

Repo layout: `train.py` (main loop), `models/Koopman/{StateAutoEncoder,ActionEncoder,ControlMatrix,
StateTransitionMatrix,LossFunction,KoopmanBuffer,Koopman}.py`, `models/Agent/{Actor,Critic,PPO,ReplayBuffer,
RewardNormalizer}.py`, `test.py`, `sample/` (pretrained actor.pth + state_encoder.pth), MIT-licensed.

---

## Route verdict

**The page-image route worked completely.** All 22 pages rendered via `pdftoppm -png -r 150` (page 19 also
at 400 DPI) and were readable via the Read tool with no OCR needed — text, equations, tables, and figures
all legible directly. This resolved every target the text-layer route (FlateDecode-garbled `pdftotext`)
could not reach, including the two passages (Algorithm 3's stop-gradient operator, the Draeger 1995
topological-conjugacy paragraph in Appendix G) that are pure vector/embedded-font content invisible to
naive text extraction.

---
NOTE (durable copy): rendered page caches (kippo_pages/) were job-scratch and are not shipped; regenerate via pdftoppm -png -r 150 from arXiv 2505.14566.
