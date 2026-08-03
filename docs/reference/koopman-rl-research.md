# Koopman x RL Integration Research — Consolidated Reference

**Date**: 2026-08-03. **Status**: research phase CLOSED (3 adversarial critique-research rounds,
early-stopped at round 3 of a 4-round budget). **Scope**: what is known, with what evidence, about
integrating Koopman-operator ideas into the constrained-albc teacher-student RL stack — at a level
sufficient to plan experiments and write code without further literature research.
**Out of scope by owner directive**: experiment planning (rosters, budgets, branches, thresholds) —
that is the next stage's job (`exp-design`); see §7.

**Provenance**: produced by an iterative adversarial process — original survey + analyses (T-RO
survey full read, 7-category integration survey, 3-axis variants survey, citation deep-reads,
sim-to-real sweep), then three rounds of {4-lens adversarial critique -> targeted research}. Every
round attacked the previous round's outputs; five load-bearing claims made by the rounds' own
research reports failed later primary-source checks, and one Round-1 critique claim (its Bruder
characterization) was itself snippet-contaminated and corrected by the round-1b page-image read.
Working log with full round records:
[`koopman-rl-research/working-log-2026-08-03.md`](koopman-rl-research/working-log-2026-08-03.md)
(PART II, §17-20; the `.sp/plans/` original is scratch).
**Evidence base**: per-topic research/critique reports copied to
[`koopman-rl-research/`](koopman-rl-research/) next to this file (44 reports + the working log). Citations below carry
verification-depth tags: **[FT]** full text read, **[IMG]** page-image read (rendered PDF pages read
visually — used where text layers were corrupt), **[ABS]** abstract/partial, **[SNIP]** search
snippet only. Snippet-depth claims are never load-bearing in this document.

---

## 1. Verdicts on the two original proposals

**Proposal 1 — lift ALL network inputs (o_t, p_t, commands, history) into a Koopman observable
space before the encoder + policy, to improve implicit system identification: NOT SUPPORTED as
stated.** Three independent reasons survived all rounds: (a) lifting `p_t` is vacuous — 25 of its
28 dims are constant within an episode (code-pinned: `ou_enable=False` shipped, no override in the
repo; only `p_t[25:28]` measured lin-vel varies), so there are no dynamics to linearize; (b)
commands/actions enter dynamics nonlinearly even after lifting, and a *predictive* operator has no
law by which to advance exogenous commands (the survey's joint-lifting hazard — scoped: action
*history* inside `o_t` as a policy input is fine and is rigorously part of the delay-system state);
(c) `o_t` already embeds 46-52D of delay history, so a "pointwise lift" of it is already a
short-window history encoder — the proposal adds an unlearned lifting in front of a learned one.
Additionally, the claimed mechanism is now closed empirically at the literature level: latent
representations trained with reconstruction+prediction losses do NOT reliably encode low-variance
plant parameters (§3, recon_context findings), so "better implicit system identification" is not
what such a lift would deliver. What *survives* is a narrower variant the proposal did not state —
lift `o_t` only, keep the encoder, z bypasses the lift — as arms C/D in §4, with one weak precedent
(KIPPO) and strict controls.

**Proposal 2 — drop the encoder and student; Koopman-lifted obs + base policy alone: NOT SUPPORTED**
(unchanged through all rounds, argument corrected). The correct argument is structural, not
information-theoretic: removing the encoder and student removes the only explicit parameter channel
(z), while a pointwise transform of `o_t` adds no new information — and whether the
~9-physical-step embedded history is sufficient for implicit identification is an OPEN
observability/excitation question, not a settled impossibility (window-length-vs-parameter-
timescale reasoning is a non-sequitur; §4-J). The data-processing-inequality version of this
argument ("carries exactly the information, therefore cannot help") was retracted as overreach —
information-preserving transforms can and do change optimization geometry; that is precisely
KIPPO's claim. The honest empirical test, if ever wanted, is the `NoEncoder` vs `NoEncoder+phi_x`
pair — noting that NO NoEncoder run exists on the current plant (the registered task is not a
baseline; the only artifact is April full-DOF, pre-TAM/pre-buoyfix).

---

## 2. System facts that gate every design (code-anchored, verified this investigation)

1. **p_t time-variance**: 25/28 dims constant per episode. Time-varying: `p_t[25:28]` (measured
   body lin-vel, policy-driven state). `p_t[19:22]` ocean current is constant per episode as
   shipped (`config.py:556 ou_enable=False`, no `=True` anywhere; `payload_toggle_steps=0`); water
   density `p_t[18]` constant. The 34D fault variant adds 6 more per-episode constants.
   Consequences: any "dynamics of z/p_t" objective has K≈I as its optimum (verified empirically,
   §4-J1); parameter-probing of representations must use per-episode DR labels ACROSS episodes,
   not within-episode variation.
2. **Teacher z logs exist only in student-mode eval** (`eval.py` student-mode `latent_*.npz`);
   there is no teacher-training z log. Offline z analyses must source from there or from new
   eval passes.
3. **Trust-region code constraints** (`_core/algorithms/constraint_trpo.py`): parameter grouping is
   by name prefix (`:161-184`) — anything not starting with `critic./cost_critic./value_backbone./
   reward_head./cost_head.` lands in `_policy_params` (the TRPO natural-gradient vector); K/B/H or
   any module used only in an aux loss inside `_policy_params` **crashes** `_flat_grad(...,
   allow_unused=False)` (`:354-366`); `storage.clear()` (`:526`) runs before the only runner hook,
   so any aux step must be inserted inside `ConstraintTRPO.update()`; the KL is evaluated by
   re-running the policy forward against stored `old_mu/old_sigma/old_logp` recorded at rollout
   time — an out-of-band representation update changes the policy with no KL budget consumed AND
   makes the stored behavior stats stale (biased surrogate before the trust region even applies).
4. **Value loop destroys temporal pairs**: `_update_values` shuffles `torch.randperm` over the
   flattened (T*E) batch. Any one-step prediction loss needs its own pair-preserving sampler over
   unflattened `storage.observations` with `dones` masking (+ the last-step bootstrap-obs gap).
5. **Critic API**: `evaluate()/evaluate_costs()` take obs only — an action-conditioned prediction
   input (SKooP-style) requires an API change at 3+ call sites; critic obs are recomputed, not
   stored; added channels change `num_critic_obs` -> critic normalizer geometry + `_init_base`
   assertions.
6. **Normalizer**: `EmpiricalNormalization` drift is 1/k-annealing (asymptotically self-freezing at
   4096x64 samples/iter) and the constructor takes `until=N` (hard freeze, one kwarg). Its
   `_mean/_std` keys are a **frozen deploy contract** with 6 consumers (teacher geometry inference,
   deploy export specs + engine + golden parity + CLI, student instance-sharing, tests) — do not
   replace the module; o_t bounds are NOT DR-derivable (integral/bias-EMA are policy-dependent
   accumulators).
7. **Downstream geometry**: a phi_x inside the policy passes all 4 training-side dim checks (env
   obs width unchanged, fresh track fine) but breaks `FrozenTeacher` (hardcoded architecture;
   same-width lift loads silently WRONG under `strict=False` — the 38d979e failure class),
   `actor_forward` used by both student losses, and the deploy export contract
   (`actor.0.weight == (256, obs_dim + latent_dim)`), and phi_x weights have no export spec.
   An actor-side lift is trainable but neither distillable nor exportable until those are extended.
   (Anchors: `_core/student/teacher.py:114-136` hardcoded arch + `:143` non-strict load + `:186-194`
   `actor_forward`; `deploy/specs/teacher_actor.py:14-15,26-42` normalizer/width contract;
   `deploy/engine.py:66,167` obs-dim inference.)
8. **Encoder-health diagnostics** assume the encoder slice is contiguous and everything else is
   "actor": a module named `encoder*` corrupts `Grad/enc_step`; any new module silently inflates
   `Grad/actor_step`. Name new modules `lift_*` and add an explicit slice.
9. **Real-vehicle observability**: IMU + pressure only (no DVL — surge/sway unobservable), obs bus
   <= 25 Hz ZOH, joints 10 Hz, 2/6 thrusters currently faulted. Any sim-vs-real operator comparison
   is confined to the rotational+heave delay-embedded subspace and must match ZOH staleness at the
   data-generation stage (no post-hoc metric fixes it).
10. **Settled project rules that bind designs**: no auxiliary losses on the p_t->z encoder (any
    aux gradient path into it — e.g. an un-detached K(z) hypernetwork — violates the rule's letter
    and is an ordering-dependent silent bug vs `value_optimizer.zero_grad()`); algorithm =
    ConstraintTRPO+IPO settled; screening = single-seed ~2000 iters.
11. **Trajectory artifacts on disk**: `eval static` writes `data_<level>.npz` (attitude/rate/joint
    channels + scalar action summaries + per-env `dr_*` labels; assembled `eval.py:883-936`); the
    full policy-obs vector is saved only under `--save-policy-obs` (off by default) and the applied
    8D action sequence is never logged. Full-obs EDMD or phi_x pretraining (§4-A2/A4) therefore
    needs a fresh eval/collection pass with `--save-policy-obs` plus an action log (new output file
    per the B0 instrument-isolation rule), not just existing logs.

---

## 3. Theory foundations and empirical closures

**Survived all three rounds:**
- Koopman linearity is a property of time evolution under fixed dynamics, never of the obs->action
  map (survey §II; the original review's central and correct point).
- Exact-realizability results (affine vs bilinear vs control-coherent; [97] Cor II.1, KCF, CCK) are
  MODEL-ROLE results. For a representation-shaping aux loss (never rolled out), realizability does
  not decide the form — affine-vs-bilinear is a post-signal ablation, not a prerequisite. CCK's
  transferable content is the phantom-pathway failure mode (regression-fit B invents impossible
  instantaneous control->state paths, invisible in prediction error, catastrophic under closed-loop
  exploitation) — a structural-sparsity discipline for any hand-designed dictionary.
- ESC filter + actuation latency is a Markovity requirement on phi_x's input (o_t's action-history
  and ESC-state blocks must cover the actuator memory), not a model-form problem.
- A single K across the DR family assumes one jointly-invariant subspace across all plants —
  stronger than any cited theorem provides. Under fault-scale regime change this is the standing
  central risk ("single-K blocker"). The 2026 Ocean Eng fault paper does not refute it: it fits K
  on nominal dynamics only for residual generation and delegates compensation to a reconfigured
  classical controller [ABS].
- Trust-region + concurrently-drifting representation is an UNSOLVED, unprecedented combination:
  no published work pairs auxiliary representation learning with TRPO/NPG-family hard-KL optimizers
  (searched hard, twice); KIPPO itself drifts phi_x *during* PPO epochs behind a stop-grad and
  survives on PPO's clip tolerance — there is no safe-cadence recipe to borrow, only options to
  design (§5 rule 6). PFO/Moalla is an adjacent-mechanism warning (PPO-clip-specific), not proof
  for hard-KL either way.
- Invariance-pressure hypothesis (a shared prediction operator prefers plant-invariant features):
  legitimate mechanism, supported by ONE adjacent result (IIDA [FT], scope-noted) after two of its
  three original supports failed primary-source checks (CaDM's matched effect is 1.1-3.5x not 4-7x;
  the IB ablation removes the whole objective, not just preservation). Carried as a weakened
  "re-weighting risk" pre-registered prediction, not an established effect.

**Closed empirically (zero GPU cost, this investigation):**
- **J1 — student Koopman-consistency term is dead**: least-squares K fit on logged teacher z
  (student-mode eval latents) is not distinguishable from the identity — ||K - I||_F below the
  split-half refit spread at every stride and DR level. Scope of the closure: one run, one
  checkpoint (trpo_sdeint_c2_daggersel_s30_260729_185634 static eval), student-in-loop static-eval
  distribution — not the teacher's on-policy training distribution; pairs were not done-masked
  (masking can only shrink ||K-I||, so the direction is safe); 84 latent_*.npz exist repo-wide, so
  cross-run replication is a 5-minute numpy job. The proposed loss
  `||K z_t - z_{t+1}||^2` is a temporal-smoothness penalty in disguise, with no Koopman content,
  and would fight the episode-start identification transient. CLOSED.
- **Plant symmetry**: the 6-thruster allocation matrix is exactly C2-equivariant under
  port-starboard reflection with thruster permutation (12)(34)(56); the planar 2-link arm preserves
  it; per-episode DR draws break it per-realization while preserving it in distribution (the form
  DHA-style methods need). Gate for the DHA lead: a cheap offline C2-equivariance probe on logged
  rollouts, before reading further.

**Closed at the literature level:**
- No published work isolates the linearity constraint — KIPPO's own ablations never swap K for a
  nonlinear MLP; TD-MPC2 is existence-proof that unconstrained latent-consistency scales without
  it. Any ALBC result without a nonlinear-latent control arm cannot be attributed to "Koopman".
- Latent representations trained with reconstruction+prediction do NOT reliably encode low-variance
  plant parameters: theory (reconstruction -> top singular vectors of obs covariance =
  variance-driven selection), a direct probing study (arXiv 2607.27017: recon- and
  prediction-trained latents both at R^2 ~ 0.12-0.13 for drag vs 0.89 raw-data ceiling; July-2026
  preprint, not peer-reviewed), and
  PrivilegedDreamer's own ablation (reconstruction-only RSSM worst at hidden-parameter recovery;
  explicit estimation head required). Consequence: an o_t lift neither delivers "implicit sysID"
  (upside claim dead) nor catastrophically strips theta (z carries it explicitly and bypasses the
  lift) — the only honest hypothesis for an actor-side lift is optimization geometry, which is all
  KIPPO ever claimed.
- Gating the context/estimation path is settled practice, not a dispute: CaDM feeds context from a
  frozen pretrained model as a NumPy array (outside the RL graph entirely); PrivilegedDreamer's
  estimator lives in the world-model loss with actor/critic trained against a *fixed* world model;
  WMR cuts the gradient explicitly and carries an ablation showing the cutoff is necessary.

---

## 4. Design space (per-item cards)

Ordering is by evidence-and-cost structure, not preference. Every training arm's REQUIRED CONTROLS
are part of the card — an arm without its controls is uninterpretable.

### A. Offline analyses — zero training risk, run before/independent of any arm

- **A1. K-vs-I on logged z** — DONE, negative (§3 J1). Method (reusable): collect z sequences from
  student-mode eval; fit K by least squares per stride/DR level; decision statistic =
  ||K - I||_F vs split-half refit spread.
- **A2. Sim-vs-sim spectral diagnostic**: EDMD (delay-embedded, [pykoopman/pykoop]) on logged sim
  rollouts, compared ACROSS DR arms/levels — none of the sim-vs-real confounds (partial obs, ZOH
  mismatch, closed-loop distribution shift across datasets) applies within one simulator under a
  matched eval protocol. Decision use: regime discrimination (per-terrain spectral signatures
  precedent [53]) and a quantitative handle on "how different are the DR corners the policy sees".
  Measured caveat (feasibility run on existing eval z-latents): ||K_none - K_hard|| = 1.24 at
  stride 25 vs split-half noise floors 1.68 (none) / 0.06 (hard) — at low DR the comparison is
  dominated by fit variance; compute the per-level split-half floor before reading any cross-arm
  delta. Full-obs EDMD needs the §2.11 collection pass (existing logs lack policy obs + actions).
- **A3. C2-equivariance probe** on existing eval logs (gate for the DHA lead, §4-H).
- **A4. Offline phi_x+K pretraining study** on logged rollouts + a scripted-excitation collection
  pass (minutes of sim wall-clock; the RL loop never sees the excitation data): sweep latent m,
  observe recon/prediction plateaus, measure per-dim variance and effective rank of the learned
  block. Feeds arms C and D; identifiability caveat: offline fits are only well-identified along
  directions the logging policy excited — the scripted-excitation portion is load-bearing
  (identifiability cluster: 2605.09545, 2511.03734, 2605.17966).
- **A5. theta-probe protocol** (the health gate's core): ridge/linear probe from a frozen
  representation (z, or phi_x latents, or the student GRU hidden state) to per-episode DR labels
  across episodes, with a degenerate-baseline R^2 floor. This is also the direct measurement of the
  invariance-pressure question (§3) — cheaper than any training arm and decision-grade.

### B. Physics-informed feature augmentation arm (restored; the low anchor)

Append ~6-8 hand-designed marine observables to o_t: sin/cos of roll/pitch, signed-quadratic rates
`omega|omega|` (per-DOF quadratic-drag shape; recurs in both physics-informed marine Koopman papers
[90][150]), optionally current-state cross terms ([87]-style). Cheapest possible arm: obs-builder
edit, no module, no aux loss, no optimizer or trust-region contact; rule-compliant (input change).
Role: the low-anchor control for the entire program — if this captures most of any lift's gain, the
learned-lift program is not worth its complexity. Expectation from theory: null-to-small.
Caveats: dictionary growth is not monotone (survey p.1091 counterexample); dims must be added to
the obs contract and deploy path like any obs change (obs4-pattern). Edit site: the policy-obs
builder in `mdp/observations.py:42-86`, assembly + width assert `albc_env.py:1118-1178`, obs-width
materializer pattern `config.py:683-724` (the bias-EMA/obs4 precedent).

### C. Frozen pretrained phi_x arm (the middle rung; semi-novel)

Pretrain phi_x (+K, B, decoder) OFFLINE on A4's corpus; FREEZE; train ConstraintTRPO from scratch
on `cat([phi_x(EmpNorm(o_t)), z])` (z bypasses the lift). No aux loss during RL (input change under
the project's own rule axis), single-variable vs baseline. Zero trust-region contact holds ONLY if
phi_x is applied OUTSIDE `self.policy`'s module tree (obs-path/runner transform):
`_policy_params` is built by iterating `self.policy.named_parameters()` with no requires_grad
filter (`constraint_trpo.py:161-184`), so even a frozen `lift_*` submodule registered on the policy
joins the natural-gradient vector (crash via `allow_unused=False`, or silent line-search
participation) — that placement costs a prefix-exclusion edit; §5 rule 4 binds this arm too.
- Precedent status: semi-novel combination; pieces precedented separately (ATC pretrain+freeze
  [visual, analogy only]; DeepKoopman offline AE fits; RMA phase-2 freezing) [ABS].
- Known failure mode (published): staleness — a frozen module trained on early/pre-collected state
  distributions degrades on late-policy states; A-RMA's third phase exists precisely for this.
  Health gate must track recon/pred error of the frozen phi_x on live rollout data over training;
  a drift-up is the arm's honest failure signature (and itself informative about C-vs-D).
- Anti-collapse: expansive AE + reconstruction (KIPPO branch). Identity-inclusion is
  undecided-but-disfavored — not for KIPPO's exact-realizability reason (wrong argument class for
  a regularizer), but because the identity block re-imports raw-state nonlinearity into the K-fit
  block and lets both aux losses look healthy while the learned part is inert (this project's own
  decoder-shortcut failure class). Working practice exists on both sides ([50],[86] use it; KIPPO
  rejects it).
- m sizing: precedents run larger-is-better to saturation (KIPPO sweep {16,32,48}, +64 in its
  300-config analysis, best value per-env — HalfCheetah still improving at 48, InvertedPendulum
  plateauing past 32; OFENet expansive; [50] coverage>dimension). "Try smaller m first" is an
  untested inference — choose m from A4's plateau, not from priors.
- Deployment staging (pre-round record, never contested through all rounds): a sim-trained phi_x is
  FROZEN at deployment and never re-fit on real data (moving-target hazard at deploy); only a
  model-role operator (K in observer/model uses) gets a cheap real-data refit. The published
  pattern is freeze-the-lifting / refit-the-operator (Kinova 2603.03740 A,B-only fine-tune [FT];
  Bruder IJRR K_p + gamma*K_r blend — prediction RMSE 0.07 combined vs 0.14 physics-only vs 0.21
  data-only, pure-data MPC failed outright [IMG]); no real-data sample-efficiency curve exists for
  that recipe (confirmed by direct read).
- Required controls: same-size frozen NONLINEAR latent-dynamics phi (linearity isolation) and/or
  frozen random expansion (expansion-vs-structure); arm B as the low anchor.

### D. Concurrent actor-side arm (KIPPO-adapted) — research-program class, not a screening arm

Everything in C, plus phi_x trains during RL. This is novel-method territory: no aux-representation
+ hard-KL precedent exists anywhere; the KIPPO recipe (single Adam, joint loss, stop-grad only,
drift during epochs) relies on PPO clip tolerance that ConstraintTRPO does not have.
- Update-protocol options (all unvalidated under hard-KL; each a design decision): (1) freeze-phase
  cadence — phi_x steps only BETWEEN TRPO iterations (PPG-pattern [FT]: "infrequent auxiliary
  phases are critical"), with old_mu/old_logp/z_old re-anchored after each phi step (repairs the
  stale-surrogate defect directly); (2) EMA/stop-grad target encoder (SPR-pattern [FT]: target
  vital, 0.415->0.278 without; tau=0 pure stop-grad peaked WITH data augmentation, whose role SPR
  attributes to representational diversity — mapping that onto 4096-env DR diversity is our
  extrapolation, not a verified transfer); (3) PFO-style representation penalty added
  to the objective [FT] (adjacent-mechanism precedent only).
- Loss recipe from KIPPO [IMG]: L_KI = 0.75*L_rec + 0.1*L_pred-latent + 0.5*L_pred-state, horizon
  swept only over H in {1,3,5,10} (per-env best never above 10; the paper's main text separately
  recommends "8-32 steps" — an internal inconsistency unsupported by any of its tables); keep the
  TRIPLE intact — KIPPO's own ablation shows subsets are
  the negative cells (no state-space prediction => negative on ~4/6 envs; omega_3 < 0.25 loses the
  benefit). Unbundle ARCHITECTURE add-ons (bilinear H term, z-conditioned K(z)) as later ablations;
  do not unbundle loss terms.
- If K(z) is ever added: z.detach() into the hypernetwork is mandatory (rule letter + silent-grad
  bug §2.10); gating is settled practice (§3); MamKO [FT, ICLR 2025, openreview hNjCVVm0EQ] is the
  closest mature architecture (Mamba-generated time-varying Koopman triple, diagonal A,
  negative-CELU stabilized, ZOH-discretized — MPC-side, not RL); MAKO [FT, arXiv 2510.09042] is
  the nearest inferred-context analog but fits per-task discrete operators, not a continuous
  function of a latent — K(z) still has no exact precedent.
- Implementation surface: param ownership decided by name (`lift_*` + extend `value_prefixes` or
  grouping logic — otherwise TRPO sweeps it in / `allow_unused` crashes); aux step inserted in
  `update()` before `storage.clear()` with its own pair-preserving sampler + done masking;
  aux loop MUST minibatch (Kronecker/H-term intermediates at the flat 262k batch OOM a 12 GB
  4070); phi_x sits inside ~25 policy forwards/iteration including 10 CG double-backprops — a
  measured ms/iter gate belongs in any proposal; encoder-health slices (§2.8).
- Precedent strength + screening-length risk: one 4-seed PPO no-DR precedent whose per-env effect
  is positive on 2/6 envs, neutral on 2/6, and negative-until-late on 2/6 ("surpasses the baseline
  towards the end") [IMG Fig C.1]; the headline +6-60% mean return and 26.89-91.43% variance
  reduction vs PPO are end-of-training aggregates with one exception (HalfCheetah-v4, +16.76%
  variance) [IMG]; its defaults come from a 7,200-model hyperparameter search. A 2000-iter
  single-seed screen sits in the regime where KIPPO loses on a third of its own suite — interpret
  nulls accordingly.
- Pre-registered predictions (record before launch): theta-encoding in phi_x ~ null (§3);
  invariance-pressure = re-weighting risk, measured by A5 probe on the trained phi_x.
- Required controls: nonlinear-latent twin (same size, same loss weights, K -> MLP), trained
  NoEncoder baseline (does not exist on current plant), arm B low anchor.

### E. Critic-side variant (SKooP-adapted) — demoted, conditional

SKooP feeds a one-step privileged Koopman prediction to the critic only; motivation is
deployment-cost avoidance, not a demonstrated actor-side failure (no actor-side ablation exists)
[FT]. On this stack the "structurally safe" story is only conditionally true: value-group
membership is a name-prefix string; `evaluate()` has no action argument (SKooP's a_t-conditioned
prediction needs an API change); critic obs are recomputed and dim-checked; the aux model build
cost is the same as D minus the protocol question. Evidence prior: our critic is already privileged
(28D p_t + 9D z) — IAAC [FT, ICML 2026] shows stacking more privileged signal onto an informed
critic has no guaranteed marginal value and can hurt; the value-expansion diminishing-returns
result [FT] points the same direction (directional analogy only). A null at screening scale cannot
be distinguished from underpowered. Status: keep only if redesigned around an informative outcome
(e.g., paired with A5 probes showing the prediction contains information the critic's current
inputs lack), with the same nonlinear-latent control.

### F. Student architecture = SSM framing (the "Koopman student", properly named)

A Koopman-linear recurrent student IS a deep SSM. The SSM literature settles what a hand-built
Koopman student would re-derive: stable diagonal/HiPPO parameterization, ZOH discretization
(matches the real 25 Hz ZOH bus semantics), O(log N) parallel-scan training, and RL episode resets
(Resettable S5 with proof) [FT, Lu et al. NeurIPS 2023 — S5 outperforms GRU while training ~6x
faster on memory tasks].
Robot distillation precedent: REAL [FT] uses a Mamba student at a 10-frame window (our scale) with
a large ablation win and latency under budget — but NO GRU/TCN baseline exists anywhere: a
GRU-vs-SSM-student head-to-head on the observability-retrain roster would be original evidence.
Counter-evidence: Mamba causal-conv asymmetry bias [SNIP, 2509.17514]. Interaction cost: the deploy
pack currently supports only the single-layer-GRU head (albc-deploy memory) — an SSM student needs
a new export path + goldens before it is deployable; that cost belongs in any proposal.

### G. Deployment-time observer line (medium-term; unchanged, now with a marine fault precedent)

Online Koopman disturbance/current observer as a student extra-obs channel (obs4-pattern,
sim-consistent, export-spec required). Primitives: SSSD (streaming SSD, fixed memory, Thm 6.3
equivalence) [FT, arXiv 1909.01419 = survey ref [31]]; DHC's guard patterns (freeze on rank
deficiency; correction vanishes at nominal) [FT]; OM-Koop field-validated marine online Koopman
[ABS]; EVOLVER embedded-feasible observer [FT]. NEW: Ocean Eng 348 (2026) 123965 [ABS] —
nominal-K FDI residual observer + separately reconfigured controller on an 8-thruster UV with
unknown injected faults: a platform-class precedent for detection-side Koopman that does NOT
require one K to model post-fault dynamics. Full text unreachable (ScienceDirect); re-fetch before
citing details.

### H. Symmetry lead (DHA) — gated

Dynamics Harmonic Analysis ([131] real content: symmetry-equivariant Koopman via isotypic
decomposition, Mini-Cheetah validated) [ABS] — untested beyond quadrupeds; not a manipulator/UUV
precedent. Our plant qualifies structurally (§3 C2 fact) in distribution. Gate: A3 probe first;
read DHA in full only on a positive result.

### I. Gap meter (sim-vs-real spectral distance) — deferred, protocol recorded

Deferred: not "applicable-now"; a defensible protocol exists but is real engineering with
unvalidated axis-attribution, and a DR-support coverage check on trajectory statistics answers the
operative question ("is the real plant inside the trained envelope") more directly. If ever built:
closed-loop-aware estimator (closed-loop DMD bias is real [ABS, Dahdah & Forbes 2303.15318; repo
decargroup/closed_loop_koopman]); replay real input sequences + initial conditions in sim (removes
distribution mismatch; converts the residual risk into a SHARED identifiability weakness unless the
data has excitation — a stochastic policy's dither helps quadratically [FT, 2605.17966]);
subspace-restrict both fits to the identical delay-embedded IMU+pressure observable set with a rank
check (surge/sway claims impossible); match ZOH staleness at the replay stage (no metric fixes it
post-hoc; continuous-time eigenvalue renormalization log(mu)/dt fixes CLOCK rate only, demonstrated
on one synthetic system [FT, SGOT 2509.24920]); fault-match the plant (2/6 faulted); noise-floor
controls = K_sim-vs-K_sim across seeds AND across DR draws. Distinguish the two "coverage check"
costs: trajectory-statistics coverage from existing logs is cheap; parameter-fitting coverage
(e.g. a real decay-test) is a new constrained hardware experiment.

### J. Closed / dropped (with reasons — do not silently resurrect)

- **J1 student Koopman-consistency term**: CLOSED empirically (K≈I on logged z; §3).
- **Koopman as DR replacement**: no support anywhere; Koopman components complement DR at most.
- **Critic replacement (KEEC/KARL-style) and sim-surrogate world models**: our 4096-env GPU sim is
  the cheap side; surrogates replace expensive generators.
- **Offline RL symmetry augmentation (KFC-style)**: no offline dataset; teacher is on-policy.
- **Reward-shaping Koopman-Lyapunov actor terms**: the one clearly-harmful variant in LC-SAC
  (-93/94%). The rest of LC-SAC: no evidence of benefit on the closest analog (quadrotor,
  overlapping 5-seed bands), variance benefits on cartpole — "not a supported direction absent a
  mechanism argument", not a blanket prohibition.
- **HVOK/delay-embedding infrastructure and teacher-side history windows**: dropped for the RIGHT
  reasons — no RL-actor precedent and the student GRU already integrates history; the earlier
  "window must match parameter timescale" premise was a non-sequitur (constant parameters have no
  timescale; identifiability is set by excitation/observability — RMA's 50-step adapter is the
  counterexample).
- **Whole-body Koopman-MPC safety filter**: blocked on compute reality — 0.21913 s/step (~4.6 Hz;
  the paper states no compute platform) for a fixed-base 7-DoF arm [FT, corrected from a fabricated
  25 Hz figure], vs our <=25 Hz embedded bus for a coupled vehicle+arm.
- **p_t lifting / command joint-lifting**: §1 Proposal 1 reasons.

---

## 5. Cross-cutting design rules (bind every arm)

1. **Gate every context path.** z.detach() into any conditioning module (rule letter); the
   literature uniformly gates (CaDM frozen-numpy / PrivilegedDreamer fixed-WM / WMR ablation-backed
   cutoff).
2. **Loss-triple integrity; unbundle architecture only.** (KIPPO Fig D.1/E.3.)
3. **Every Koopman arm ships with its non-Koopman twin.** The linearity constraint is the only
   Koopman-specific testable content and no paper isolates it; without the nonlinear-latent control
   (and arm B as low anchor) results are unattributable.
4. **Naming and ownership.** New modules `lift_*`; decide TRPO-vs-Adam ownership explicitly against
   the prefix list; extend the encoder-health slices.
5. **Pair-preserving aux sampler** inside `update()` before `storage.clear()`, done-masked,
   minibatched. Never ride the randperm value loop.
6. **No concurrent phi_x update without a protocol** chosen from D's option list; freeze-phase +
   re-anchoring is the default recommendation (repairs the stale-surrogate defect by construction).
7. **Normalizer**: keep the module; `until=N` if freezing is wanted. Static min-max is only valid
   for DR-sampled quantities (p_t), not o_t.
8. **Health gates precede verdicts** (z_sweep discipline extended): per-dim variance floor on the
   learned block; effective-rank/capacity check; A5 theta-probe vs degenerate baseline; staleness
   drift for frozen modules. A gate must be able to fail (name the defect that trips it).
9. **Screening-length honesty**: 2000-iter single-seed screens sit inside KIPPO's behind-until-late
   regime; a null there is weak evidence. State this in the proposal, not after the run.
10. **Unreadable PDFs**: render pages (`pdftoppm -png -r 150`) and read images — this investigation
    recovered three load-bearing papers (KIPPO appendix, Bruder IJRR, PrivilegedDreamer) that way
    and caught a snippet-contaminated claim in its own review chain.

---

## 6. Known-unknowns register (closable only by experiments, not by more research)

1. Does ANY latent-dynamics aux representation help on-policy hard-KL RL under DR? (No precedent
   exists; the entire on-policy evidence base is thin — OFENet PPO 5/5 wins but 3/5 within seed
   noise; KIPPO 4 seeds; Voelcker theory is fixed-policy DQN/TD3.)
2. Linear (Koopman) vs nonlinear latent-dynamics constraint, all else equal — genuinely open
   everywhere; our control-arm pair would be the first direct test.
3. Invariance-pressure vs null on theta-correlated features under our DR (A5 probe decides cheaply).
4. Frozen-vs-concurrent phi_x (C vs D) — staleness vs drift trade, no published comparison.
5. GRU vs SSM student at our window/scale — no head-to-head exists in the literature.
6. Marginal value of any aux feature to an already-privileged critic (IAAC says "not guaranteed";
   our case untested).
7. Whether the C2 symmetry survives in logged closed-loop data strongly enough for DHA-style
   structure to bite (A3 decides).

## 7. What the next stage (exp-design) must add — deliberately absent here

Per owner directive this document contains no experiment plan. The next stage owns: adoption/
rejection thresholds tied to eval decision_floors; wall-clock/GPU budgets and two-machine
allocation; branch + baseline tag per the comparison-experiment isolation rule; wandb
group=project naming; teacher plant/sha to branch from (worktree-base rule: branch from the run
manifest's git.sha); arm rosters and sequencing against the live campaign backlog (obs4/c4b
launch gate, curriculum recalibration, latency-DR lead and the other open omx leads are a separate,
already-designed queue — Koopman arms compose with, and must not displace, that queue without an
explicit user decision).

---

## 8. References (load-bearing; grouped; verification depth tagged)

### Primary survey + companions
| Ref | Depth |
|---|---|
| Shi, Haseli, Mamakoukas, Bruder, Abraham, Murphey, Cortes, Karydis, "Koopman Operators in Robot Learning", IEEE T-RO 42:1088-1107 (2026); arXiv 2408.04200. Local: `/workspace/references/Koopman Operators in Robot Learning.pdf` | FT |
| KoopmanRobo companion tutorial (unicycle EDMD + affine input + cvxpy MPC), `/workspace/references/KoopmanRobo/` | FT (code) |

### Koopman x RL precedents
| Ref | Depth |
|---|---|
| Cozma, Harris, Qi, "KIPPO: Koopman-Inspired PPO", IJCAI 2025, pp.4994-5002; arXiv 2505.14566. MS-thesis provenance: trace.tennessee.edu/utk_gradthes/11783 | IMG (22 pp) |
| SKooP (critic-only symmetric Koopman predictions, Cyberdog 2), arXiv 2607.11624; repo evelyd/SymmetricKoopmanPredictions | FT |
| LC-SAC (Koopman-Lyapunov SAC, quadrotor/cartpole), arXiv 2602.04132 | FT |
| DKRL (Song et al. 2021, local Koopman, LQR-side), arXiv 2010.07546 | FT |
| KFC / Koopman Q-learning (offline symmetry, ICML 2022) | FT (via survey round) |
| Plotzki & Peitz, Koopman surrogate for RL of Rayleigh-Benard, arXiv 2603.28074 (no "Dyna-Koopman" name) | FT (report) |
| KORR, arXiv 2509.12562; RK-MPC (Go1); Residual KMPC (F1TENTH) | FT (reports) |

### Self-predictive / aux-representation mechanism class
| Ref | Depth |
|---|---|
| OFENet, Ota et al., ICML 2020, arXiv 2003.01629 — PPO on 5/5 MuJoCo tasks, wins 5/5 (2 large: Hopper +44%, HalfCheetah +39%; 3 within noise); repos merlresearch/OFENet, BY571/OFENet | FT |
| Voelcker et al., "When does Self-Prediction help?", arXiv 2406.17718 — fixed-policy-eval theory, DQN/TD3 empirics | FT |
| SPR, Schwarzer et al., arXiv 2007.05929 — target/stop-grad vital (0.415->0.278), tau=0 peak w/ augmentation | FT |
| PPG, Cobbe et al., arXiv 2009.04416 — alternating phases, KL-clone term, "infrequent aux phases critical" | FT |
| PBL, Guo et al., ICML 2020 (IMPALA) | ABS |
| TD-MPC2, arXiv 2310.16828 (nonlinear latent consistency at scale; MPPI-centric) | FT |
| Ni et al., "Bridging State and History Representations", arXiv 2401.08898 | ABS |
| No Representation No Trust / PFO, Moalla et al., NeurIPS 2024, arXiv 2405.00662 — PPO-clip-specific; repo CLAIRE-Labo/no-representation-no-trust | FT |
| SAC-AE 1910.01741; DreamerV3 | ABS |

### Context/DR-conditioned dynamics + privileged learning
| Ref | Depth |
|---|---|
| CaDM, Lee et al., ICML 2020, arXiv 2005.06800 — matched shared-vs-conditioned gap 1.1-3.5x; context frozen/numpy into PPO; repo younggyoseo/CaDM (TF1.15) | FT + code |
| T-MCL arXiv 2010.13303; ProtoCAD arXiv 2211.12774 | ABS |
| IIDA, arXiv 2203.05549 (conditioned loss clusters env identity; supervised/offline scope) | FT |
| IB sim-to-real, arXiv 2305.18464 (privileged-alignment term helps; no compression-isolating ablation) | FT |
| PrivilegedDreamer, arXiv 2502.11377 — estimator in WM loss, actor/critic vs fixed WM; recon-only RSSM worst at parameter recovery | IMG |
| WMR, arXiv 2502.16230 — gradient cutoff verbatim + ablation-backed | FT |
| RMA (Kumar et al. 2021), A-RMA (phase-3 unfreeze = staleness precedent), HORA | ABS |
| MAKO, arXiv 2510.09042 (per-task operators over shared lift) | FT |
| PVKO, arXiv 2309.10278 (known-parameter conditioning) | ABS |
| IAAC, "Informed Asymmetric Actor-Critic", arXiv 2509.26000, ICML 2026 — richer privileged critic signal can hurt | FT |
| Value-expansion diminishing returns, arXiv 2412.20537 | FT |
| FCSRL, arXiv 2405.11718 (cost-critic value-consistency: workable-but-weaker) | FT |
| Recon-vs-prediction parameter probing, arXiv 2607.27017 (drag R^2 0.12 vs 0.89 ceiling; July-2026 preprint, not peer-reviewed) | FT (r3 report, HTML) |

### Koopman theory / input handling / marine (survey citation deep-reads)
| Ref | Depth |
|---|---|
| [36] KCF (Th 4.3 / Lemma 4.5 input-state separable taxonomy); [105]; [161] switched forms; [162] | FT (cluster reports) |
| [97] Bruder/Fu/Vasudevan bilinear realization, arXiv 2010.09961 — Cor II.1; decimals are figure-reads | FT |
| [37] Control-Coherent Koopman, arXiv 2403.16306 — phantom-pathway ablation | FT |
| [43] input-scaled disturbance bilinear NMPC, arXiv 2504.21215 | FT |
| Underwater row [87][88][89][90][150] (marine dictionaries: signed-quadratic velocity terms, arctan ratios, current cross-terms) | FT (cluster report) |
| [78] KEEDMD episodic; [84] DHC online DMDc w/ guards; [86] KoopNet frozen-at-deployment | FT (cluster report) |
| [50] Incremental Koopman, arXiv 2411.14321 — anti-collapse concat, light recon 0.1, coverage>dimension; repo intelligent-control-lab/Incremental-Koopman | FT |
| [31] Haseli & Cortes SSD/SSSD, arXiv 1909.01419 (fixed-memory streaming; Thm 6.3) | FT |
| [131] Ordonez-Apraez et al., DHA, L4DC 2024, arXiv 2312.07457 (symmetry-equivariant Koopman) | ABS |
| [53] Krolicki et al. (per-terrain Koopman spectra), IFAC 2022 | ABS |
| Lusch/Kutz/Brunton DeepKoopman, Nat. Comm. 2018; repo BethanyL/DeepKoopman | ABS |
| Bruder, Bombara, Wood, residual Koopman soft arm, IJRR 2025, doi 10.1177/02783649241272114 (NTRS OA copy) — analytic prior + EDMD residual, gamma-blend; data-driven-only MPC failed outright; NO real-data efficiency curve; online update = future work | IMG (17 pp) |
| Whole-body KMPC (Kinova), arXiv 2603.03740 — 0.21913 s/step (4.6 Hz); A,B-only real-data fine-tune | FT |
| SGOT spectral-Grassmann-Wasserstein, arXiv 2509.24920; repo thibaut-germain/SGOT | FT |
| Closed-loop Koopman ID, Dahdah & Forbes, arXiv 2303.15318; repos decargroup/{closed_loop_koopman,pykoop}, dynamicslab/pykoopman | ABS |
| Behavior-policy identifiability, arXiv 2605.17966 (deterministic-feedback degeneracy; dither quadratic gain) | FT |
| Koopman identifiability cluster, arXiv 2605.09545, 2511.03734 | ABS/SNIP |
| Hankel-DMDc ship sysID, arXiv 2502.15782 (full state, NOT partial-obs precedent) | FT |
| OM-Koop (field USV/AUV online Koopman, IEEE 11123429); EVOLVER (T-RO 2024, STM32 observer); K-ESKF (IROS 2024) | ABS/FT (reports) |
| Akumalla, Kadiyam, Jain, "Actuator fault-tolerant control of underwater vehicle using koopman framework", Ocean Engineering 348 (2026) 123965 — nominal-K FDI + reconfigured backstepping, 8-thruster UV, unknown faults | ABS (full text unreachable) |
| KODex CoRL 2023; KOROL arXiv 2407.00548; KOAP arXiv 2410.07584 (plan-then-control; stripped variant untested) | FT (reports) |
| Safety row: Koopman-CBF (Folkestad CSL 2021), Neural Koopman CBF (ACC 2023), robust filter arXiv 2605.26452, KTMPC, conformal reachability arXiv 2601.01076 | FT/ABS (reports) |
| Sim-to-real row: digital twin arXiv 2409.10347 (-5.2%); FADA arXiv 2606.28476 (~2-min IDM fine-tune); Split Koopman arXiv 2502.00162; DMD-GEN arXiv 2412.11292 | ABS |

### SSM / student architecture
| Ref | Depth |
|---|---|
| Lu et al., "Structured State Space Models for In-Context RL" (Resettable S5), NeurIPS 2023, arXiv 2303.03982 — resets/HiPPO/ZOH/parallel-scan solved; S5 outperforms GRU while training ~6x faster | FT |
| MamKO, Li/Han/Yin, ICLR 2025 (openreview hNjCVVm0EQ) — Mamba-generated time-varying Koopman triple for MPC | FT |
| REAL, arXiv 2603.17653 — Mamba student in privileged distillation, 10-frame window; no GRU/TCN baseline | FT |
| LocoMamba, arXiv 2508.11849 (end-to-end RL backbone, not distillation) | ABS |
| Mamba asymmetry bias, arXiv 2509.17514 (NeurIPS 2025) | SNIP |
| Bilinear Mamba-Koopman NMPC arXiv 2605.04793; Koopman-bilinear Mamba arXiv 2604.17221 | SNIP |
| ATC, Stooke et al. 2021 (pretrain+freeze, visual); DynE, Whitney et al. 2019 (joint, state-based) | ABS |
| Reward-free offline latent dynamics, arXiv 2502.14819 | ABS |

### Degeneracy guards / probing
| Ref | Depth |
|---|---|
| VICReg, arXiv 2105.04906 (variance/covariance floors — apply to learned block only) | ABS |
| Mamakoukas stable Koopman, arXiv 2005.04291 | ABS |
| Draeger et al. 1995 (topological conjugacy, via KIPPO App G) | IMG (quote) |
| KIPPO-PyTorch-Unofficial (Bluehorse-hub) — STRUCTURALLY DIVERGES from Algorithm 3; disqualified as implementation reference | code-read |

## 9. Evidence-report index

All per-topic reports (44 files) are in [`koopman-rl-research/`](koopman-rl-research/):
`paper_p*` (survey read), `albc_report`/`code_report` (code maps), `survey_*` (7-category round),
`axis_*` (3-axis round), `cluster_*`/`table1_*`/`s2r_*` (citation deep-reads),
`r1_critique_*` / `r1_research_*` / `r1b_*_imageread` (round 1), `r2_critique_*` (round 2),
`r3_research_*` (round 3). The full working log with all round records and verdict-change tables is
copied alongside as `working-log-2026-08-03.md` (original at
`/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md`, scratch).
