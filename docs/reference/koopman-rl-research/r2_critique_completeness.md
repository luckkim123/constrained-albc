# Round-2 critique — lens: COMPLETENESS

Target: `/workspace/.sp/plans/2026-08-03-koopman-lifting-analysis.md` (978 lines, PART I §1-16 + PART II §17-18).
Bar being audited (owner's words): *"experiment planning and code implementation must be possible from this doc
WITHOUT further research."*

Verdict up front: **the doc does not meet that bar for any §18.9 item except #3, and #3 I closed during this
review** (ran it — result below). The gap is not literature coverage; after Round 1 the literature is in
reasonable shape. The gap is (i) no item is specified to the level where code can be written without
re-deriving decisions from the codebase, (ii) the doc's entire evidentiary base lives in an ephemeral job
directory, and (iii) three whole framings were never considered, one of which has a 2026 marine paper sitting
exactly on the axis the doc repeatedly calls unprecedented.

Symmetric-skepticism note: I attacked Round-1 outputs and the doc equally, and where I could settle a question
with code or data rather than argument I did (four such settlements below: the K-vs-I fit, the p_t
time-varying slice, the `_update_values` shuffle, the critic-obs plumbing).

---

## 0. Findings I settled with evidence during this review (not opinions)

| # | Question the doc leaves open | Settled how | Answer |
|---|---|---|---|
| E1 | §18.4 item 4 / §18.9 item 3: is the teacher-z operator K distinguishable from I? | Ran the least-squares fit on 4 existing `latent_*.npz` artifacts | **NO, at any stride, at all 4 DR levels. Item closes.** |
| E2 | Round-2 open item: exact p_t time-varying slice (theory said 6, systemfit said 4) | `envs/main/mdp/observations.py:89-205` docstring + `torch.cat` order | **6 of 28: `[19:22]` ocean current (world xyz) + `[25:28]` measured body lin-vel. 22 constant. In the 34D fault variant, `[28:34]` thruster health is also per-episode constant → 6 of 34.** Theory lens was right. |
| E3 | §18.7 "critic-side input changes live entirely in the Adam-owned value group" | `algorithms/constraint_trpo.py:161-184` | **Conditionally true, and the condition is a naming string.** Group membership is decided by `name.startswith(p)` over `("critic.", "cost_critic.", "value_backbone.", "reward_head.", "cost_head.")`. A submodule named `koopman.` lands in `_policy_params` = the TRPO natural-gradient vector — the exact silent-double-ownership failure Round 1 catalogued for the actor side (§17.1-1(ii)) reappears on the "safest" arm. |
| E4 | Can a Koopman aux loss ride the existing value-update loop? | `constraint_trpo.py::_update_values` | **No.** It shuffles `torch.randperm(batch_size)` over the (T·E)-flattened batch — temporal adjacency is destroyed in every value minibatch. A one-step prediction loss needs its own pair-preserving sampler built from the *unflattened* `storage.observations` (T, E, ·) + `storage.dones` before `storage.clear()` (line 526). |

### E1 in full (this is a result, not a plan)

Data: `experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_c2_daggersel_s30_260729_185634/
eval/static_260729_190943/latent_{none,soft,medium,hard}.npz`, key `l_true` = teacher `encode_privileged(p_t)`,
shape (7751, 64, 9), float32, one static-eval rollout per DR level, DR frozen per env at rollout start
(`eval.py:775` "now-fixed DR").

Fit: pool all envs and times, `K = argmin_K ||X K - Y||_F` with `X = z_t`, `Y = z_{t+s}`; compare against the
identity predictor; noise floor = split-half refit `||K1 - K2||_F` (first vs second half of the pairs).

Stride sweep, `latent_none`:

| stride s (steps) | ‖K−I‖_F | split-half ‖K1−K2‖_F | RMSE(K) | RMSE(I) | gain over identity |
|---|---|---|---|---|---|
| 1 | 0.120 | 0.167 | 0.00190 | 0.00191 | 0.6% |
| 5 | 0.425 | 0.543 | 0.00486 | 0.00494 | 1.6% |
| 25 | 1.247 | 1.676 | 0.01456 | 0.01512 | 3.7% |
| 50 | 1.515 | 2.130 | 0.01871 | 0.01971 | 5.1% |
| 100 | 2.048 | 2.489 | 0.02477 | 0.02709 | 8.6% |

All four DR levels at s=1: gain over identity 0.0% / 0.1% / 0.0% / 0.6% (hard/soft/medium/none),
diag(K) = 1.000 ± 0.01. At s=25 the split-half floor exceeds ‖K−I‖ at every level
(none 1.68 > 1.25, soft 0.46 > 0.31, medium 0.099 > 0.069, hard 0.061 > 0.038).

**Reading**: the fitted operator's departure from identity is smaller than the fit's own sampling variability
at every stride and every DR level. K is not distinguishable from I on this data. §18.8 row 4's salvage path
is exhausted: the student Koopman-consistency term is confirmed vacuous, empirically, at zero GPU cost —
which is exactly what §18.4 item 4 promised the check would do.

**Caveats I will not hide** (these belong in the doc if the result is adopted):
(a) one run, one checkpoint, student-in-loop static eval — not the teacher's on-policy training distribution;
(b) I did not done-mask: envs can terminate mid-eval (`terminated` array exists in `data_<level>.npz`) and
Isaac Lab auto-reset re-randomizes, so a small number of pairs straddle a discontinuity. Masking can only
*reduce* the apparent K−I deviation, so the conclusion is robust in the direction that matters;
(c) 84 `latent_*.npz` files exist repo-wide (`find /workspace/constrained-albc -name 'latent_*.npz'`), so
replication across runs is a 5-minute numpy job, not an experiment.
(d) the doc says "already-logged teacher z" as if it were a general artifact. It is not: `l_true` is written
**only** in student mode (`eval.py:1499-1502`, gated on `is_student_mode`). There is no teacher-training z log
anywhere. An implementer following the doc would go looking in the training logs and find nothing.

---

## (a) Coverage audit — what an implementer hits that the doc cannot answer

### Cross-cutting gaps (hit before any specific item)

1. **The evidence base is stored in a job-scratch directory.** §17 and §18 delegate every substantive
   justification to `$CLAUDE_JOB_DIR/tmp/r1_*.md` (11 files, ~300 KB) and PART I delegates to
   `tmp/{survey_*,axis_*,cluster_*,table1_*,s2r_*,paper_p*}.md` (another 20). Those live under
   `/root/.claude/jobs/add36792/tmp/`, and the doc itself lives in `/workspace/.sp/` which the workspace rules
   declare gitignored throwaway scratch. **Nothing load-bearing is in a durable store.** For a doc whose bar is
   "no further research needed", the reference lists + verification depths must be *in* the doc (or the reports
   copied into the repo / omx wiki). This is the single largest completeness defect and it is spec-only to fix.
2. **No decision rule anywhere.** Not one item states what result would cause adoption, what would cause
   rejection, or what would be inconclusive. §8.4 lists metrics ("gradient variance / KL health / convergence
   speed at fixed iter + eval static") but no thresholds, and the project's own convention is that eval
   `summary.json` declares `decision_floors` — none are named here. Without this, every arm's outcome is
   re-litigated after the fact.
3. **No cost model.** Wall-clock per arm, GPU allocation, and the two-machine (workstation + DGX) split that
   every ALBC roster is supposed to carry are absent. §18.8 row 2 says the 4-arm screen is 4 new runs (not 2)
   and §18.10 says KIPPO's defaults came from a 7,200-model search — both are cost statements with no budget
   attached. An owner cannot schedule this.
4. **No campaign placement.** Which `<group>` / wandb project? Which branch and baseline tag (the workspace rule
   *requires* `baseline-<YYMMDD>-<topic>` + `exp/<topic>` before any code-modifying experiment)? Which teacher
   plant (the E-int teacher trained at `max_thrust (0.85,1.15)`, and `main` does not carry gate D-a)? None of
   this is in the doc, and all of it is mandatory before launch.
5. **No opportunity-cost comparison.** The doc ranks Koopman arms against each other, never against the
   project's actual next experiment (the observability retrain). The operative decision is "does any Koopman arm
   outrank the standing backlog", and the doc cannot support that comparison because it never states expected
   effect sizes in the project's own metric units.

### Item-by-item

#### §18.9-1 — Critic-side Koopman prediction probe (SKooP-adapted) → **needs-spec**

The doc gives a paragraph. Implementing it requires answering all of these, none of which need new literature:

| Q | Why the doc can't answer it |
|---|---|
| Predict *what*? | SKooP predicts its own lifted state. Ours could be: next `o_t` (OFENet-style raw), next 20D dynamic block (§10 Axis B), next `p_t` time-varying slice `[19:22]+[25:28]`, or next `phi(o_t)`. §18.7 says "one-step privileged Koopman prediction" without naming the observable set. The choice determines whether the arm is Koopman at all. |
| Produced by which model, trained on what? | An autoencoder `phi` + operator (K,B[,H])? Trained on which stream — the same on-policy rollout, a replay buffer (§16.3(a) argues for one), or a separate excitation pass (§16.1)? |
| Which optimizer, at which cadence? | SKooP uses a decoupled optimizer + PER buffer. Ours has exactly two groups (TRPO-functional, Adam-value). A third optimizer is a new object in `ConstraintTRPO.__init__`; a shared one means the aux gradient rides `max_grad_norm` clipping with the critics. |
| Named how? | **E3**: the prefix string decides whether the module is TRPO-stepped or Adam-stepped. Must be `value_backbone.` (or a new prefix explicitly added to `value_prefixes`). |
| Injected where in code? | `_get_critic_obs()` (`actor_critic_encoder.py:264-275`) builds `cat([o_t, (z), p_t])` at update time from the stored obs TensorDict — critic obs are *recomputed*, never stored. Two options: extend `_get_critic_obs` (self-contained, but see next row) or add an env obs key (touches the obs contract, dim checks, and possibly the student/deploy path). |
| Conditioned on `a_t`? | SKooP's critic input is `z_{k+1} = A f(x_k) + B u_k` — it needs the action. **`evaluate(obs)` and `evaluate_costs(obs)` have no action argument** (`_policy_base.py:139-153`), and they are called from rollout (`constraint_encoder_runner.py:153,172`) and from `_update_values`. Feeding a genuinely one-step-ahead prediction means changing the RSL-RL critic API at 3+ sites, or degrading to `a_{t-1}` (already inside `o_t`'s 16D action history) and accepting that it is not SKooP's quantity. The doc's "structurally safest, zero contact" claim does not survive this. |
| Stop-grad? | Does the value MSE backprop into the Koopman AE? SKooP says no policy gradient into the AE; the doc never states the value-gradient decision. Note the precedent hazard in-repo: `critic_uses_z=True` already routes value gradient into the encoder and required an explicit params-group fix (`constraint_trpo.py:186-193`). |
| Aux loss trained on which pairs? | **E4**: not the value minibatch loop. Needs (o_t, a_t, o_{t+1}) pairs from unflattened storage with `dones` masking, before `storage.clear()`. |
| Normalization? | `critic_obs_normalizer` is `EmpiricalNormalization(num_critic_obs)`; adding channels changes `num_critic_obs` → changes checkpoint geometry and the `_init_base` dim assertions. Is the prediction normalized, and by what? |
| Checkpoint / deploy | Deploy rebuilds the teacher via `_infer_teacher_dims` from `actor_obs_normalizer._mean` and loads non-strictly (`deploy/engine.py:52-190`), so an extra critic-side module is *tolerated* — but that is contingent on strict=False and on the golden-parity contract (closed at 2f057b9) still passing. "No deploy contact" should be stated with that contingency, not flatly. |
| Ablation partner | SKooP-NoPred (lifted state instead of prediction) is the paper's own control and is worse late-stage. Is our probe run with it? Two runs or one? |
| Success criterion | Given the honestly-stated null prior, what value-loss / return / KL delta would count as a positive? Unstated. |

#### §18.9-2 — Actor-side phi_x screening arm → **needs-research AND needs-spec**

Round 1 already established that the update protocol has no precedent (§18.2: "no published pairing of aux
representation learning with TRPO/NPG-family optimizers exists at all") and Round 1b removed the last
borrowable recipe (§18.10: KIPPO's "decoupled" is stop-grad inside one joint loss, no between-iteration
cadence). So this arm is novel-method work. What the doc still cannot answer, in the order an implementer hits
them:

- Which of §18.2's four mitigations, with what constants? Freeze cadence in iterations? Re-anchor
  `old_mu/old_logp` where in `update()` (before `_trpo_step`, after)? PFO coefficient (its "power-of-10-matched"
  rule is PPO-loss-scale-specific and our surrogate has an IPO barrier term in it).
- `phi_x` architecture: width/depth, activation, output bound. §11.3's "try smaller m first" was downgraded
  (§18.8 row 7) but no replacement value of m is named.
- Does the actor see `cat([phi_x(o_t), z])` or `phi_x` alone? KIPPO's actor sees **only** `y_t` with no raw
  concat (§18.10), which conflicts with §11.1's settled "z bypasses phi_x, concatenated raw". The doc holds both
  and never reconciles them.
- Normalization: §18.8 row 6 withdrew the normalizer swap, and §18.10 records KIPPO states *no* input
  normalization before `phi_x`. So: `EmpNorm(o_t) → phi_x`? Raw `o_t → phi_x`? Where does `actor_obs_normalizer`
  (dim `policy_obs_dim`, migration logic in `load_state_dict`) sit relative to the lift? Unspecified, and it is
  a checkpoint-geometry decision.
- Loss weights: KIPPO's 0.75/0.1/0.5 (Table B.2) came from a 7,200-model search on MuJoCo. Transfer rule? None.
- The mandatory controls (nonlinear-latent predictor; frozen-random expansion; trained NoEncoder baseline) are
  named but not sized — that is 3-5 additional runs whose cost is never stated.
- Pre-registration: §18.8 row 2 says "record the prediction before launch". The prediction text does not exist
  in the doc.

Research-needed residue: whether *anyone* has since paired aux representation learning with a hard-KL
optimizer (Round 1 searched and found nothing; worth one confirmation pass, not a re-survey), and verification
of the unofficial-KIPPO-repo disqualification (§18.10 already did this).

#### §18.9-3 — Offline K-vs-I check → **was needs-spec; now DONE (see E1)**

The doc could not answer: which runs, which z, what least squares, what threshold. All four are answered above,
and the check is executed. The remaining half of item 3 ("optional offline `phi_x`+K fit on logged rollouts to
sanity-check m and loss scales") is still **needs-spec**: it requires logged `(o_t, a_t, o_{t+1})`, and the only
on-disk obs log is `data_<level>.npz`'s optional `policy_obs` key (`eval.py:163`, off by default) — i.e. no
existing artifact has it, so a fresh eval with `--save_policy_obs` is a prerequisite the doc never mentions.

#### §18.9-4 — Deployment observer line → **needs-research (newly reopened) + needs-spec**

Newly relevant literature the rounds missed (see perspective audit (iv)) lands directly here: a 2026 Koopman
*actuator-fault-tolerant* framework on an 8-thruster UV, and a 2025 online-Koopman-tuning FTC paper explicitly
about minimal sensor information. Both bear on the doc's repeated "no Koopman work validates under
actuator-fault regime switching" and on the IMU+pressure observability constraint. Spec side: no channel
definition (what does the observer output, in what units, at what rate, ZOH-held how), no sim-side
counterpart (obs4's rule is train/deploy channel identity), no export-spec delta.

#### §18.9-5 — Gap meter → correctly deferred; **known-unknown, not a worklist item**

§18.6's reclassification is sound and I do not contest it. One completeness note: the DR-coverage check it
recommends *instead* is named but never specified either (which parameters, which real datasets, what
coverage statistic). And `data/` is host-side and unreachable in-container (§11.6 says this) — so the item is
gated on a host session that has not been scheduled.

#### §18.9-6 — Recorded leads → mixed

DHA: **needs-research (small)**, see below. OFENet comparator: **spec-only** (it is the nonlinear-latent
control arm under a different name — the doc lists them as separate items in §18.1 and §18.9-6 without noticing
they collapse). PrivilegedDreamer/WMR stop-grad A/B: **spec-only**, and moot unless K(z) is pursued.

---

## (b) Perspective audit — framings Rounds 0-1 never considered

### (i) DHA / symmetry-equivariant observables — worth a probe, not dead on arrival

Verified source (abstract-level, arXiv:2312.07457): Ordoñez-Apraez, Kostic, Turrisi, Novelli, Mastalli, Semini,
Pontil, *"Dynamics Harmonic Analysis of Robotic Systems: Application in Data-Driven Koopman Modelling"* — the
state space of a **symmetric** robot decomposes into orthogonal isotypic subspaces, each carrying an independent
linear system; an equivariant deep architecture then learns a global linear model with better generalization
and interpretability, demonstrated on quadrupedal locomotion.

Our plant's symmetry, checked against code rather than intuition (`marinelab/assets/uuv_cfg.py:158-176`, the
6×6 thruster allocation matrix ALBC inherits):

```
Fx ( 0.707,  0.707, -0.707, -0.707, 0,   0  )
Fy (-0.707,  0.707,  0.707, -0.707, 0,   0  )
Fz ( 0,      0,      0,      0,     1,   1  )
Mx ( 0,      0,      0,      0,     0.1,-0.1)
My ( 0,      0,      0,      0,     0.12,0.12)
Mz ( 0.19,  -0.19,   0.19,  -0.19,  0,   0  )
```

Under the port-starboard reflection (y→−y: Fx,Fz,My symmetric; Fy,Mx,Mz antisymmetric) with the thruster
permutation (1 2)(3 4)(5 6), every row maps correctly: Fx,Fz,My invariant; Fy,Mx,Mz negated. **The allocation
matrix is exactly C2-equivariant.** The arm (`joint1`/`joint2`, x-offsets 0.233 m, z-offset 0.1625 m — a planar
2-link chain on the centerline, `marinelab/assets/albc/albc.py:158-168`) does not break the group: reflection
maps the chain to itself (or to negated joint angles, still an equivariance). So the *nominal* plant carries a
Z2 = C2 symmetry — smaller than Mini-Cheetah's Klein-4, but real and verifiable.

Honest paragraph: what kills it is **per-episode DR, not geometry**. Payload CoG offset `p_t[11:14]` includes a
y-component, ocean current `p_t[19:22]` has a world-frame y-component, and per-thruster fault health is drawn
independently per thruster — each of these breaks the symmetry *within an episode* while preserving it *in
distribution*. DHA's payoff (independent linear systems per isotypic subspace) requires the equivariance to hold
for the realized dynamics, not just the ensemble. Verdict: not dead on arrival, but the cheapest honest probe is
offline and non-Koopman — measure whether the *trained policy* is already approximately C2-equivariant
(mirror `o_t`, permute the action, compare) and whether DR draws destroy it. That is an afternoon of numpy on
existing eval artifacts, and it gates the whole line. The doc has no such probe.

### (ii) Koopman-for-the-student ≡ a deep SSM — the framing that dissolves an "open" question

The doc treats "Koopman-linear recurrent student" (§10 Axis C's DRKO note, §9 cat-6) as an open, novel design.
It is not novel in the way the doc thinks: **a linear latent recurrence with a learned input map is exactly what
S4/S5/Mamba are**. That literature has already answered the questions the doc lists as open for a
Koopman student — how to parameterize the operator so long-horizon recurrence is stable (diagonal /
diagonal-plus-low-rank, eigenvalue placement inside the unit disk), how to initialize it (HiPPO), how to train
it at sequence scale (parallel scan instead of BPTT), and how it compares to a GRU on long-memory tasks.
Directly on point: **MamKO** (OpenReview `hNjCVVm0EQ`) generates a *time-varying* Koopman operator from a Mamba
backbone — that is our §11.1/§18.3 "K(z)" idea with a mature architecture and a published comparison against
constant-operator Koopman models; and *"Bilinear Input Modulation for Mamba: Koopman Bilinear Forms"*
(arXiv 2604.17221) is the bilinear-vs-affine question (§13.1/§18.8 row 12) asked inside the SSM literature.
Verification depth: **search-snippet only** — OpenReview served a bot-check page to WebFetch and I did not read
either paper. I flag them as leads with that depth stated, not as facts.

Why this matters for completeness, independent of whether those two papers hold up: the adopted student is a
GRU (memory: A0g/GRU adopted, lambda closed as an axis, observability retrain is next). Swapping the GRU for an
S5/Mamba-class encoder **is** the Koopman-linear student, and it (a) needs no auxiliary loss, so it never touches
the settled no-aux-loss rule, (b) has zero trust-region contact (student training is supervised distillation),
(c) rides an experiment that is already scheduled, (d) has a much larger and better-replicated literature behind
it than KIPPO's 4-seed MuJoCo result. The doc's 978 lines never consider it. Whether it *works* here is a known
unknown, but as a framing it dominates §18.9-2 on every risk axis the doc itself uses to rank arms.

### (iii) Offline / eval-side diagnostics — the §6 idea that vanished, and it is the cheapest thing here

§6 proposed "offline EDMD/HVOK analysis of logged trajectories as a diagnostic (spectral comparison across DR
arms) — analysis-only, no training-path change". Rounds 0-1 then narrowed the entire offline lane to the
sim-vs-real gap meter, which got deferred (§18.6) for reasons — partial observability, ZOH mismatch, closed-loop
bias — **that are all sim-vs-real problems and none of which apply to a sim-vs-sim comparison.** Nobody
adjudicated the sim-side version; it was dropped by attrition. That is a process gap of the same class Round 1
found elsewhere.

E1 above is an instance of this lane, and it produced a decision-grade result in minutes on existing artifacts.
Two more instances are equally cheap and equally unspecified in the doc: (1) the same K-fit run per DR level and
compared across levels — I ran it as a feasibility check (‖K_none − K_hard‖ = 1.24 at stride 25, against
split-half floors of 1.68/0.06 at the two ends), and the honest reading is that the instrument's discriminability
is **dominated by fit variance at low DR**, which is exactly the noise-floor discipline §15.3 demanded and never
operationalized; (2) the C2-equivariance probe from (i). Recommending the offline lane as a *first-class item*
rather than a footnote is the single highest value/cost change available to this doc.

### (iv) Marine Koopman 2025-2026 the rounds missed

Targeted search, not a re-survey. Two hits bear on load-bearing doc claims:

- **Akumalla, Kadiyam & Jain, "Actuator fault-tolerant control of underwater vehicle using Koopman framework",
  Ocean Engineering vol. 348 (2026), art. 123965.** Koopman model identified from operational input-output data
  during backstepping trajectory tracking → linear observer → real-time fault detection/isolation → controller
  reconfiguration; demonstrated on a fixed **8-thruster** underwater vehicle with injected actuator faults.
  Verification depth: **search-snippet, corroborated across two independent queries** (title, authors, volume,
  article number consistent); ScienceDirect returned 403 to WebFetch, so no abstract was read. If it holds, it
  directly narrows the doc's cross-cutting blocker ("no surveyed paper validates under actuator-fault-scale
  regime switching", §9) and §9 cat-5's "fault regimes untested" — on our exact platform class and our exact
  fault axis. **This is the highest-value single verification item for Round 3.**
- **"Online Tuning of Koopman Operator for Fault-Tolerant Control: A Case Study of Mobile Robot Localising on
  Minimal Sensor Information", Machines 13(6):454 (2025)**, open access. Combines the online-update mechanic
  (§9 cat-5) with the *minimal sensing* constraint that defines our deployment (IMU + pressure only).
  Verification depth: **title/venue from search results; MDPI returned 403 to WebFetch.**
- Also surfaced and not in the doc: EnKode (arXiv 2410.16605, active learning of unknown flows with Koopman
  operators) — relevant to the ocean-current observer channel; "Optimizing AUV speed dynamics with a data-driven
  Koopman operator approach" (arXiv 2503.09628, ROS2/Gazebo validation).

Note the asymmetry this exposes: PART I's underwater row was read at depth from the survey's bibliography, whose
window closes before 2025. The doc's marine coverage is therefore ~1 year stale on the one domain where it most
needs to be current.

### (v) A framing nobody raised at all: the comparison class

Every arm in this doc is compared against other Koopman arms. None is compared against the non-Koopman
intervention that would achieve the same claimed mechanism — OFENet for "expansive aux-dynamics features"
(§18.1 already knows this and files it as a control arm, not as the framing), TD-MPC2-style unconstrained latent
consistency (§18.1 names it as an existence proof and drops it), an SSM student for "linear latent dynamics"
(above). If the linearity restriction is the only Koopman-specific testable content (§17.1-2, and I agree), then
the doc's ranking is answering "which Koopman arm" when the owner's question is "is Koopman worth an arm at
all". That reframing is spec-only and would change §18.9's ordering.

---

## (c) Reference hygiene — §18 claims not traceable to a named source with stated verification depth

The doc states verification depth **zero times in §18**; §18 delegates it wholesale ("each with full reference
lists + verification depth" → the tmp reports). Under the owner's bar that is a defect regardless of whether the
underlying claims are right. Specific untraceable-as-written items:

| § | Claim | Missing |
|---|---|---|
| 18.1 | "On-policy evidence for the whole aux-dynamics class is SPARSE, not negative (PBL/IMPALA closest)" | PBL has no ID; "no PPO/TRPO-scale negative results found" is an unbounded negative with no search scope stated |
| 18.2 | Options (1)-(4), "PPG-pattern", "SPR-pattern" | Named by pattern, no citations, no IDs |
| 18.2 | "No published pairing … exists at all (searched hard)" | Search scope/date not recorded; this is the load-bearing claim that makes item 2 novel-method work |
| 18.3 | CaDM "4-7x", IB-sim-to-real "almost fails", IIDA clustering | IDs present, depth absent (abstract? full text?); §18.9's own open-items list already flags these for spot-verification, which concedes the point |
| 18.4 | "no source reports active harm from over-expansion (saturation only)" | Unbounded negative, sources searched not enumerated |
| 18.6 | 2303.15318 / 2605.17966 / 2502.15782 / 2509.24920 | Depth absent; 2502.15782's "full state not partial obs" is a content claim that requires having read it |
| 18.7 | 2412.20537 "even an ORACLE model barely helps", FCSRL 2405.11718 | Depth absent |
| 18.7/18.9-1 | "code-verified zero contact with trust region / deploy / student" | Contradicted in part by **E3** (naming-dependent) and by the `evaluate()` signature; deploy-safety is contingent on strict=False |
| 18.10 | KIPPO page-image read | The *only* place in §18 where depth is explicit ("pdftoppm 150dpi + vision") — this is the standard the rest should meet |
| 17.1-10(i) | "[131] mis-resolved … never read" | Now partially closable: I verified DHA at abstract level (arXiv:2312.07457, authors + isotypic-subspace/equivariant-architecture content) — still not a full read |

Also: PART I §9's table and §13-15 carry numeric claims (e.g. "[97] linear error flat ~0.55-0.60 … bilinear
~0.03-0.05", "74.3 cm vs 2.03 cm") that Round 1 flagged as figure-reads rather than stated text (§17.1-8). The
doc records the flag in §17 but the numbers still sit unmarked in §13.1 where a reader will meet them first.
Superseded-claim marking is by cross-reference only; PART I is never annotated in place. For a 978-line doc
whose own header says "the later section governs", that is a live foot-gun.

---

## (d) Round-3 worklist

**Spec-only** (writable from existing material; no new sources):

| ID | Item | Notes |
|---|---|---|
| S1 | Move the evidence base into a durable store | Copy the 11 `r1_*` + `r1b_*` reports (and the PART-I `tmp/*.md` set) into the repo or the omx wiki; replace `$CLAUDE_JOB_DIR` references with real paths. Highest priority: everything else is built on files that will be garbage-collected. |
| S2 | Write the critic-side probe to pseudocode | Answer the 13 rows in (a)-§18.9-1. Must include: module name prefix (E3), pair sampler + done-masking (E4), `evaluate()`-signature decision, stop-grad decision, normalizer decision. |
| S3 | Write the actor-side arm protocol to pseudocode | §18.2 option choice + constants; reconcile §11.1 (z bypasses, raw concat) against §18.10 (KIPPO actor sees only `y_t`); name m; name loss weights and their transfer rationale; write the pre-registered invariance-pressure prediction. |
| S4 | Add decision rules + cost model + campaign placement | Per arm: metric, threshold, inconclusive band, wall-clock, GPU, group/project name, branch + baseline tag, teacher plant/sha. |
| S5 | Fold E1/E2 into the doc and close §18.9-3 | Include the split-half noise-floor method as the general threshold recipe for any K-vs-I question; correct "already-logged teacher z" to the student-mode-only reality; correct the p_t time-varying slice to `[19:22]+[25:28]`. |
| S6 | Promote the offline sim-side diagnostic lane to a first-class item | Specify the DR-level K comparison, the C2-equivariance probe, and the `--save_policy_obs` prerequisite for the offline `phi_x`+K fit. |
| S7 | Annotate PART I in place | Mark every superseded §4-§16 claim at its own location, and mark the figure-read numbers in §13.1 as figure-reads. |
| S8 | Merge the duplicated control arm | OFENet comparator (§18.9-6) and the nonlinear-latent control arm (§18.1) are the same run. |
| S9 | Add the comparison-class framing | State explicitly that the question is "is a Koopman arm worth it vs the non-Koopman alternative achieving the same mechanism", and re-rank. |

**Research-needed** (new sources required):

| ID | Item | Why |
|---|---|---|
| R1 | Verify Akumalla/Kadiyam/Jain, Ocean Eng. 348 (2026) 123965 at abstract-or-deeper | Would narrow the doc's most-repeated blocker (no Koopman validation under actuator faults) on our exact platform class. Paywalled — try DOI landing, author page, IIT Mandi repository, or the page-image route on any preprint. |
| R2 | Verify the Machines 13(6):454 (2025) online-tuning FTC paper | Minimal-sensor + online-Koopman + fault — the deployment-observer item's closest match. Open access, so a fetch route exists (MDPI 403'd WebFetch; try the PDF endpoint or `curl` + `pdftoppm`). |
| R3 | Verify MamKO + the Mamba/Koopman-bilinear paper | Decides whether the SSM framing (b)(ii) is a mature lane or a hunch; MamKO also bears directly on K(z). |
| R4 | Spot-verify Round-1's load-bearing new citations | Already on §18.9's own open list: CaDM 4-7x, 2412.20537, 2605.17966, IIDA, PrivilegedDreamer/WMR. One pass, abstract-level, with depth recorded. |
| R5 | One confirmation pass on "no aux-representation + hard-KL pairing exists" | The claim that makes §18.9-2 novel-method work; Round 1 searched once. Cheap to re-check, expensive to be wrong about. |
| R6 | Read DHA (2312.07457) properly if the C2 probe (S6) comes back positive | Gated — do not read it first. |

**Known unknowns — NOT closable by research, only by running experiments** (register, do not put on a worklist):

1. Whether an actor-side `phi_x` helps, is null, or hurts on *our* plant under DR. The invariance-pressure
   argument (§17.1-4) is a mechanism, not a prediction with a magnitude; no literature can settle it because no
   paper runs aux-representation learning under this kind of DR with a hard-KL optimizer.
2. Whether the critic-side probe moves anything, given an already-privileged critic. The
   diminishing-returns analog (2412.20537) makes null the prior; only a run distinguishes null from small.
3. Sensitivity of any KIPPO-derived arm to its 7,200-search-tuned hyperparameters on a different plant,
   algorithm, and action space. Untransferable by construction.
4. Whether K(z) beats a single K, and whether stop-grad into the hypernetwork helps or hurts (literature is
   split — PrivilegedDreamer vs WMR — which is itself the evidence that only an A/B settles it).
5. Whether an S5/Mamba student beats the adopted GRU here. The SSM literature establishes the architecture
   class, not its value on 25 Hz partially-observed UUV distillation.
6. The actual sim-to-real spectral gap magnitude, and whether it is decision-relevant. Requires the host-side
   watertank datasets and a scheduled host session — an access problem, not a research problem.
7. Whether the C2 symmetry survives realized DR draws strongly enough for DHA to have anything to decompose.

---

## Convergence statement

My lens has **not** converged. Round 3 is needed, but it is mostly a *specification* pass (S1-S9), not a research
pass; the research residue is small and targeted (R1-R5, with R1 the only one that could change a standing
verdict). If Round 3 runs as another literature round without the spec work, the doc will still not meet its
owner's bar.
