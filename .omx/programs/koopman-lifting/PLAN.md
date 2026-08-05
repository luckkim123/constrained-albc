# Koopman x RL — Experiment Plan (low-expectation, cheap-first)

> **STATUS 2026-08-05: REOPENED under a changed objective.** See §12 for the new phase.
>
> The 2026-08-04 closure below stands as a record of what was DECIDED, not of what was MEASURED.
> Two facts make the difference, and both were pre-registered in this document rather than
> discovered after the fact. First, **no Koopman operator was ever fitted in a training arm** —
> arm B shipped the dictionary half (7 hand-designed observables) with no `K`, so the
> Koopman-specific content, the linear evolution operator, was absent from the only training run
> the line ever produced. §5 says so itself: a null there "is evidence about *this dictionary at
> 2000-5000 iters single-seed*, **not about lifting in general**". Second, the clause that closed
> the line, §8 exit clause 2, is a **budget** decision — "arm B returns NULL **and no one is
> willing to spend the ≥15 GPU-h** that arm C's control set costs" — taken under the then-current
> owner directive in §1: *"되면 좋고 안되면 말고"*, a cheap side-bet on control gains.
>
> **The objective changed on 2026-08-05: paper contribution is now primary, control performance
> secondary** (owner, deep-interview Round 0/3). That re-prices the control set. Under a control
> goal the nonlinear twin and the random expansion are overhead paid to attribute a win; under a
> paper goal **they are the experiment** — the linear-vs-nonlinear latent-dynamics question is
> open everywhere in the literature (research doc §6 item 2: "our control-arm pair would be the
> first direct test"), and no published work isolates it, KIPPO included.
>
> **Arm B's NULL is retained unchanged** and is not re-litigated: it remains the low anchor, and
> the record below is its verdict. 2 of the 5 arms the study needs are therefore already complete.
>
> ---
>
> **2026-08-04 closure record (unchanged).** Arm B ran (`trpo_koopmanB_260804_202709`) and failed both
> pre-registered ADOPT conditions: `att_norm` `ss_error` improves past its floor at `hard` ONLY (1 of
> the required 2 levels) and regresses at `medium`, while roll `n_gt20` at `none` goes 0.00 → 20.33
> against a floor of 15. Pairing was 24/24 dr+fault keys at all four levels against both the
> pre-registered and the same-device baseline, and survival was 100 % everywhere, so the verdict rests
> on clean numbers. The failure shape is a transient one — at nominal physics the steady-state error is
> unchanged (0.4037 → 0.4003) while overshoot rises 7.96 → 13.74 pp and pitch rise time slows 23 % —
> and it is WORST at the easiest DR level, which is why it is a rejection rather than a robustness
> trade. §8's exit clause 2 was honored at the time: no Phase 2, arm C's ≥15 GPU-h not spent.
> Full record: omx wiki `koopman_phase_1_arm_b_null_marine_feature_lifting_buys_no_contro.md`,
> campaign ledger event `discarded` on `koopman_marine_obs`.

**Date**: 2026-08-04. **Owner directive**: "되면 좋고 안되면 말고", fast, not launching now.
**Input**: `constrained-albc/docs/reference/koopman-rl-research.md` (research phase CLOSED; its §7
delegates thresholds/budgets/branches/naming to this document).
**Contract**: this plan buys information at the lowest price that still yields a decision, and names
the exact point at which the whole line gets closed. It does not attempt the research-program arms.

---

## 1. What the research document already decided (not re-litigated here)

- Proposal 1 (lift all inputs incl. `p_t`/commands) and Proposal 2 (drop encoder+student): both NOT
  SUPPORTED. Dead.
- Arm D (KIPPO-style concurrent phi_x under hard-KL), arm E (critic-side SKooP), arm G (deployment
  observer), arm H (DHA symmetry): research-program class, weeks of work, unprecedented
  combinations. **Out of scope for this plan** — see §7.
- The only surviving honest hypothesis for any lift is **optimization geometry**, not implicit
  system identification (§3 of the source doc closed the sysID upside at the literature level).

What is left that is both cheap and decision-grade: the offline probes (A1/A5), the instrumentation
that unlocks the rest (A2/A3/A4), and exactly one training arm (B).

---

## 2. Sequencing against the live queue (binding)

The teacher/student queue owns the GPU and is **not displaced**:

| Slot | Work | State (2026-08-04 09:50 KST) |
|:---|:---|:---|
| done | Phase D — **two attempts**. `trpo_obs76_s30_260803_233239` is **VOID** (trained `fault.enable=false` against an E-int baseline that had it `true`; do not cite its numbers). The controlled `trpo_obs76fault_s30_260804_043926` **PASSES H1 on both clauses** (hard att_norm +0.0108 deg vs a 0.10 floor), report `diagnose-20260804-093500`. | teacher eligible for Phase E |
| done | **this plan's Phase 0 (K0 + K2)** — ran 2026-08-04, zero GPU. Both written to the omx wiki as the Phase 0 exit requires. | see §3 outcome below |
| next | Phase E re-distill | human-gated, already designed |
| then | this plan's Phase 1 (one 5 h run) | queued behind Phase E's decision |

Phase 0 of this plan needs **zero GPU** and can run at any time, including while Phase D trains.

**Phase 0 OUTCOME (2026-08-04).** K0: z recovers every plant parameter it was GIVEN — body mass
R²=0.46, CoG/CoB and payload mass 0.10–0.49, all clearing a 200-permutation shuffle floor — and
none that was withheld. All 6 `dr_lin_damp_*` and 5 of 6 `dr_added_mass_*` sit at the floor
because they are **absent from the 28D `p_t`** (which carries quadratic damping ROLL at `[7]` and
added mass SURGE at `[9]` only), not because the encoder failed. So the branch "z sits at the
floor → stop and re-plan" does NOT fire; the explicit parameter channel works, the implicit-sysID
upside stays dead, and optimization geometry is the only surviving Koopman claim — exactly what
Phase 1 screens. K2: `||K−I||_F` is below the split-half refit noise in 4 of 5 run-level pairs, so
J1's closure replicates; and the reason is structural (z encodes per-episode CONSTANT parameters,
so a one-step operator on it is the identity by construction). Do not re-run K-vs-I on `l_true`.
Wiki: `k0_theta_probe_2026_08_04_...`, `k2_replication_2026_08_04_...`.

---

## 3. Phase 0 — offline probes on existing artifacts (0 GPU-hours)

Verified available on disk: every `eval/static_*/` dir holds `data_<level>.npz` with **23 per-env DR
labels** (`dr_payload_mass`, `dr_body_mass`, `dr_payload_cog_{x,y,z}`, `dr_cob_*`, `dr_cog_*`,
`dr_added_mass_0..5`, `dr_lin_damp_0..5`, each shape `(num_envs,)`) and `latent_<level>.npz` with
`l_true`/`l_hat` shape `(T, 64, 9)` — `l_true` is the teacher z. 88 `latent_*.npz` repo-wide.

### K0 — theta-probe (source doc A5). The single highest-value cheap item.

- **Question**: does the privileged encoder's z actually encode the per-episode plant parameters it
  is supposed to encode?
- **Method**: per DR level, reduce `l_true` over a post-warmup window to `X (n_env, 9)`; ridge from
  X to each `dr_*` label with K-fold CV; pool across DR levels and across runs to lift n from 64 to
  several hundred episodes. **Two floors are mandatory**: predict-the-mean (R²=0) and a
  shuffled-label refit (9 features on 64 envs overfits without it).
- **Decision use**:
  - z clears the shuffle floor on the mass/damping labels → the explicit parameter channel works,
    the "implicit sysID" upside for any lift stays dead, and the only remaining Koopman claim is
    optimization geometry (proceed to Phase 1 knowing that).
  - z sits at the floor → that is a finding about the **encoder program itself**, independent of
    Koopman, and it outranks everything in this plan. Stop and re-plan around it.
- **Scope caveat to carry into any write-up**: `l_true` is logged under the student-mode static-eval
  distribution, not the teacher's on-policy training distribution (source doc §2.2).
- **Cost**: numpy + sklearn, minutes. No code in the training path.

### K2 — K-vs-I replication (source doc A1), free rider on K0's data load

J1 is already CLOSED negative on one run/checkpoint. Re-fit least-squares K on `l_true` for a
handful of other runs; statistic = `||K - I||_F` vs the split-half refit spread. Confirms the
closure is not a one-run artifact. ~5 minutes. Expected: unchanged (K≈I).

### Phase 0 exit

If K0 says z encodes theta and K2 replicates, Phase 0 has bought the two facts that make Phase 1
interpretable and cost nothing. Write both to the omx wiki regardless of direction.

---

## 4. Phase 0b — the one instrument change everything else needs (0.25 GPU-h)

`eval static` writes attitude/rate/joint channels + scalar action summaries. It does **not** write
the applied 8D action, and `policy_obs` only under `--save-policy-obs` (off by default). Therefore:

- **C2-equivariance probe (A3)** — needs the per-thruster action vector to test the
  `(12)(34)(56)` permutation. **Not runnable on existing logs.**
- **EDMD / phi_x pretraining corpus (A2/A4)** — needs policy obs + actions together.

Change: add `--save-action` alongside the existing `--save-policy-obs` (same additive pattern,
new key in the npz, default off so existing outputs stay byte-identical), then one instrumented
eval pass (~15 min, 64 envs). Roughly 10 lines.

Do this **only when Phase 1 is approved or Phase 2 is under consideration** — on its own it buys
nothing, and A3 only gates the DHA lead which is already out of scope.

---

## 5. Phase 1 — arm B: physics-informed marine features (the one training arm)

The source doc's low anchor, and the only arm whose cost fits the directive.

- **Change**: append ~7 hand-designed observables to the policy obs — `sin/cos(roll)`,
  `sin/cos(pitch)`, and signed-quadratic body rates `p|p|, q|q|, r|r|` (the per-DOF quadratic-drag
  shape that recurs in both marine Koopman papers [90][150]). 72 → 79.
- **Why this one**: pure obs-builder edit. No new module, no aux loss, no optimizer or trust-region
  contact, no `FrozenTeacher`/deploy-export breakage (it is an input change, the same class as the
  obs4 work already shipped on this branch). Every channel is a pure function of signals already in
  `o_t`, so it is trivially deployable — no new sensor.
- **Edit sites** (verified against code 2026-08-04; reuse the obs4 materializer pattern rather than
  inventing one): builder `constrained_albc/envs/main/mdp/observations.py:42 compute_policy_obs`,
  pre-`super().__init__()` dim computation + mismatch raise `albc_env.py:189-214`, runtime width
  assert `albc_env.py:1220`, cfg flag next to `use_extra_policy_obs` at `config.py:686` with its own
  `apply_*_obs` materializer. Keep `use_marine_feature_obs` independent of and composable with
  `use_extra_policy_obs` (which is already mutually exclusive with `use_student_extra_obs`).
- **Baseline**: **`trpo_eint_s30_rs2350_260727_195102`** (`model_4999.pt`) — E-int is a resume chain,
  and this is its final segment; the pre-resume `trpo_eint_s30_260727_160913` stops at `model_2350`
  and has **no** eval dir, so do not point at it. **No new baseline run needed**: three static evals
  already exist (`eval/static_260727_235736`, `_260728_000754`, `_260729_133417`). Confirm the
  chosen one matches arm B's eval protocol (mode, DR levels, `num_envs`) before pairing — an absent
  override flag is not proof of the same protocol.
- **Protocol**: single-seed **paired same-seed same-machine** screening (PLAN.md 11.6 item 3 /
  0b pivot). The 56% p2p seed floor is UNPAIRED and does not apply to this comparison.
- **Eval**: `eval.py static --num_envs 64 --headless`, checkpoint via the `train` symlink path,
  **no `--output_dir`** (rules/03 traps 1 and 2).
- **Pre-registered verdict** (record before launch):
  - ADOPT only if `ss_error` improves by more than one decision floor (**0.1 deg**) on ≥2 of the 4
    DR levels **and** `os_env_mean` does not regress past its floor (**10 pp**) and `n_gt20` stays
    within **15**. Per-axis + CV table per rules/03 is part of the report, not optional.
  - Anything else = NULL → record and close (§8).
  - **Expectation from theory: null-to-small.** A 2-layer MLP can already represent these pointwise
    functions; dictionary growth is not monotone (survey p.1091 counterexample).
  - **Screening honesty (source doc rule 9)**: a null here is evidence about *this dictionary at
    2000-5000 iters single-seed*, not about lifting in general. State it in the proposal, not after.
- **Cost**: 5.0 GPU-h train (measured rate 16.7 it/min at 4096 envs on the 4070) + ~15 min eval +
  analysis. One workstation slot.
- **Scope caveat**: the verdict is scoped to the current (pre-fix) plant. Six `needs-apply-before-
  retrain` leads are still open (§9); if any lands, arm B's result does not transfer.

---

## 6. Phase 2 — arm C (frozen pretrained phi_x): sketch only, hard-gated

Entered **only** if Phase 1 is positive, or K0 exposes a theta-encoding gap that changes the story.

Prerequisites and shape, recorded so the gate is a real decision and not a restart:
- Phase 0b instrumentation + a scripted-excitation collection pass (offline fits are identified only
  along directions the logging policy excited).
- Offline A4 study: sweep latent m, read the recon/prediction plateau, per-dim variance floor and
  effective rank. Choose m from the plateau, not from priors.
- **Placement is the load-bearing implementation fact**: phi_x must live on the obs path / runner,
  **outside `self.policy`'s module tree**. `_policy_params` iterates `self.policy.named_parameters()`
  with no `requires_grad` filter (`constraint_trpo.py:161-184`), so even a *frozen* submodule
  registered on the policy joins the natural-gradient vector — crash via `allow_unused=False` or
  silent line-search participation.
- Required controls (source doc rule 3, non-negotiable): same-size frozen **nonlinear** latent
  twin (linearity isolation) and/or frozen **random expansion** (expansion-vs-structure), plus
  arm B as low anchor. So Phase 2 is ≥3 runs ≈ 15 GPU-h, not one.
- Health gate: recon/pred error of the frozen phi_x on live rollout data over training. A drift-up
  is the arm's honest failure signature (A-RMA staleness).

---

## 7. Explicitly out of scope (do not silently resurrect)

| Arm | Why not here |
|:---|:---|
| D — concurrent phi_x (KIPPO-adapted) | No precedent anywhere for aux-representation + hard-KL; needs a protocol invented from scratch, an aux sampler inside `update()`, param-ownership surgery, and breaks `FrozenTeacher` + deploy export. Weeks, not a screen. |
| E — critic-side SKooP | Demoted at source; needs an `evaluate()` API change at 3+ call sites; our critic is already privileged and IAAC says more privileged signal is not guaranteed to help. |
| F — SSM/Mamba student | Genuinely interesting (no GRU-vs-SSM head-to-head exists), but a different axis from Koopman and needs a new deploy export path + goldens. Park as its own lead. |
| G — deployment observer | Medium-term, deployment-side. |
| H — DHA symmetry | Gated behind A3, which is gated behind Phase 0b, which is gated behind Phase 1. |

---

## 8. The "안되면 말고" exit (state it now, honor it later)

Close the Koopman line — write the null to the omx wiki, no Phase 2 — when **either** holds:

1. K0 shows z already encodes the plant parameters well (the sysID upside is confirmed dead) **and**
   arm B returns NULL; or
2. arm B returns NULL and no one is willing to spend the ≥15 GPU-h that arm C's control set costs.

A closed line is a result. Record it as one, with the pre-registered predictions next to the outcome.

---

## 9. Budget, machines, and backlog interaction

**Budget**

| Phase | GPU-h | Wall clock | Gate |
|:---|:---|:---|:---|
| 0 (K0+K2) | 0 | ~1-2 h analysis | none — runnable now |
| 0b (instrument) | 0.25 | ~1 h incl. code | only if Phase 1 approved |
| 1 (arm B) | ~5.3 | one overnight slot | after Phase E decision |
| 2 (arm C + 2 controls) | ~15+ | multi-day | hard-gated on §8 |

**Machines**
- Workstation GPU0 (4070, 12 GB): serial teacher queue — obs76 → Phase E → arm B. Do not contend.
- Workstation GPU1 (4060, 8 GB, idle): candidate for the 64-env eval/collection passes in parallel
  with training. **Verify VRAM headroom before relying on it** — untested for this workload.
- DGX: **do not split arm B across machines.** Cross-machine confound is a recorded incident
  (PLAN.md 11.2: the "+0.110 deg retrain delta" was machine-confounded). If DGX time is free, the
  correct DGX unit is Phase 2's three runs *together*, never a mixed arm/baseline split.

**Backlog** — nothing in this plan displaces the open queue. 11 `needs-experiment` leads (obs4/c4b,
curriculum recalibration, latency-DR, HydroRC, joint1 Stage-2, reward-sigma R6, nominal-corner
exposure, Stonefish/T200/thruster-gain, TAM) and 6 `needs-apply-before-retrain` blockers (buoy added
mass, HydroRC 016d1b1, IMU 45 deg, sim-hydro TAM moment arm, Stonefish rotational drag, TAM vertical)
remain untouched and higher-priority. Arm B is an obs-side change on the frozen current plant, so it
neither resolves nor conflicts with them — but a plant fix landing later invalidates its scope (§5).

---

## 10. Git, naming, and launch mechanics

- **Branch**: `exp/koopman-marine-obs`, cut from the obs76 run manifest sha **`636d7ed2`** on
  `exp/obs4-extraobs` (worktree-base rule: branch from the run manifest's `git.sha`, never `main`).
  Before branching, **content-diff** the plant-relevant config against E-int's `39e819a0` — a
  difference means re-anchor, because E-int is the paired control.
- **Baseline tag**: `baseline-260804-koopman` on the branch base, message naming E-int's final
  segment (`trpo_eint_s30_rs2350_260727_195102`, `model_4999.pt`) as the comparison run.
- **wandb**: group = project = one purpose string, `koopman_marine_obs`, used for both
  `--run_group` and `--log_project_name`. This is a **new purpose** — the user declares it before
  launch; do not fold arm B into `teacher_obs76`.
- **run_id**: `make_run_id` output only, tag mandatory (e.g. `koopmanB`).
- **Launch**: `/isaac-sim/python.sh scripts/train.py` (bare `python` is exit 127 in-session),
  `CUDA_VISIBLE_DEVICES` pinned, `agent.run_name` mandatory.
- **Nothing launches without explicit approval** — this plan queues, it does not fire.

---

## 11. Pre-registered predictions (record before any run)

1. K0: teacher z clears the shuffle floor on mass/damping labels (moderate confidence). If it does
   not, this plan is superseded by an encoder investigation.
2. K2: `||K - I||_F` stays inside the split-half spread on every replication run (high confidence).
3. Arm B: NULL on the adoption bar; small or no movement in `ss_error` (moderate-to-high
   confidence — this is the low anchor, and it is expected to behave like one).
4. If arm B is somehow positive, the first suspicion is not "Koopman works" but a per-axis
   trade-off hiding in the CV table (rules/03), and the report must rule that out before adopting.

---

## 12. Phase 2 (2026-08-05 reopen) — does the LINEARITY CONSTRAINT contribute?

### 12.1 This is a study, not an ablation arm

The owner's objective is a **venue-tier upgrade for a paper whose contributions already stand
without Koopman** (observability / curriculum / distillation / FTC results, 55 substantive wiki
decisions). That framing decides the design, because the three ways Koopman could enter the paper
are not equally valuable:

| Framing | Value to venue tier |
|:---|:---|
| "we added Koopman and it improved control" | High, but low probability — see 12.4 |
| "we added Koopman and it did not" (bolt-on ablation) | **Near zero.** Reads as a failed add-on occupying pages |
| **"we isolated whether the linear constraint contributes, with controls no prior work has run"** | **Holds either way** — the contribution is the isolation, not the sign |

Only the third survives a null. So the roster below is not "arm C plus its controls" — the
controls ARE the measurement, and the write-up must be framed that way from the proposal on, not
retrofitted after the result (research doc rule 9, screening honesty).

The question this study answers, stated once: **when a latent-dynamics auxiliary representation
helps on-policy RL, is the credit due to the LINEARITY of the learned operator, or merely to
having an auxiliary latent-dynamics objective at all?** No published work separates these. KIPPO
never swaps its `K` for an MLP; TD-MPC2 is an existence proof that unconstrained latent
consistency scales without linearity.

### 12.2 Arm roster — 5 arms, 2 already complete

| # | Arm | Isolates | Status |
|:--|:---|:---|:---|
| 1 | baseline (E-int `trpo_eint_s30_rs2350_260727_195102`) | reference | **DONE** |
| 2 | arm B — hand dictionary, no `K` | is a fixed nonlinear basis alone enough? | **DONE — NULL** |
| 3 | arm C — learned dictionary + learned `K`, frozen before RL | the full Koopman lift | TODO |
| 4 | nonlinear twin — same size, same losses, `K` → MLP | **linearity itself** | TODO |
| 5 | random expansion — frozen random lift, no training | expansion-vs-structure | TODO |

Arm 4 is the load-bearing one. Without it the study cannot attribute anything to Koopman, and
with it the study answers an open question regardless of sign.

### 12.3 Sequencing — buy the cheap information first

Do NOT spend the 15 GPU-h before the ~0.25 GPU-h check clears. §6 already flags this ordering and
it is now binding.

1. **Phase 0b instrumentation** (§4, ~10 lines, 0.25 GPU-h). Add `--save-action` next to the
   existing `--save-policy-obs`, default off so existing outputs stay byte-identical, then one
   instrumented eval pass. Existing logs carry neither the policy-obs vector nor the applied 8D
   action, so no offline fit is possible without this.
2. **Offline A4 study** (0 GPU beyond step 1). Fit `phi_x` + `K` on the collected rollouts plus a
   scripted-excitation pass; sweep latent `m`; read the reconstruction/prediction plateau,
   per-dim variance floor, and effective rank. Two decisions come out of it: whether a learned
   lifting produces a *meaningful* linear approximation on this plant at all, and what `m` to use
   (§6: choose `m` from the plateau, not from priors).
   **Kill gate:** if the learned lift's multi-step prediction error is not separable from the
   random-expansion control offline, stop here — arms 3–5 are not worth 15 GPU-h. This gate must
   be able to fail; state the measured separation before proceeding.
3. **Arms 3–5** (3 runs, ~15 GPU-h), single-seed paired same-seed same-machine, launched only
   after explicit owner approval (`omx queue-launch`, never auto-fired).

### 12.4 Pre-registered predictions (record before any run)

1. Arm C does **not** clear the control adoption bar. Moderate-to-high confidence. Grounds: this
   stack has no consumer of the linear structure (the lift feeds an MLP policy), the closest
   on-policy precedent OFENet wins 5/5 MuJoCo but 3/5 within seed noise, and arm B already showed
   that adding input width costs transient quality on this plant.
2. Arm C and the nonlinear twin do **not** separate past a decision floor. Moderate confidence —
   this is the study's central prediction and the one worth being wrong about.
3. `phi_x` does not encode plant parameters better than `z` does (research doc §3: recon+prediction
   latents do not reliably encode low-variance parameters; K0 already showed `z` encodes exactly
   what it was given).

### 12.5 Paper-inclusion decision rule (pre-registered — protects the main paper)

The main paper does not wait on this and does not depend on it.

| Outcome | Meaning | Paper action |
|:---|:---|:---|
| Arm C beats baseline past floors **and** beats the twin | linearity is doing work | Primary contribution section |
| Arm C beats baseline but **not** the twin | the aux latent-dynamics objective helps; linearity gets no credit | Include, but the claim is "auxiliary latent-dynamics prediction helps" — do **not** call it Koopman |
| Neither beats baseline, but C and twin **separate** from each other | linearity changes something that does not reach control | Methods subsection, controlled negative |
| Nothing separates (flat) | the axis is inert at this scale | **Do not include as a contribution.** One limitations paragraph at most. Do not delay submission |

### 12.6 Verdict hygiene (this project's own paid-for lessons)

- Read **survival before accuracy** — an arm that kills envs makes its deltas survivorship-biased.
- Count the **sign pattern across all cells**, not the flag list; per-cell floors do not aggregate.
- Verify pairing (`dr_*` keys identical at every level) as a gate BEFORE reading any delta, and
  again as a second gate if any arm draws RNG the others skip.
- The decision floors declare themselves paired; these arms are teacher-vs-teacher on the same
  seed and machine, so the precondition holds — state that it was checked, do not assume it.
- Per-axis + CV table (rules/03) is part of the report, not optional.

### 12.7 Open design decision, to be settled before arm C is specified

**Where is the linearity consumed?** If `phi_x`'s output is simply concatenated to the policy
input, the linear operator `K` never acts at inference and the arm degenerates toward arm B with a
learned basis. Candidate consumers, in increasing order of cost: (a) feed `K phi_x(o_t)` — the
one-step *prediction* — as an extra policy input; (b) use the prediction residual as a deployable
observer/FDI channel (the arm G line, where linearity genuinely earns its keep); (c) linear MPC —
ruled out on compute (0.219 s/step measured vs the ≤25 Hz embedded bus). Option (a) is the
cheapest that keeps `K` in the loop and is the current default. Settle this before writing the
arm C proposal.
