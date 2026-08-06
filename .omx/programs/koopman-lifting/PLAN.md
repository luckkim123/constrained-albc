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

## 0. Resume here after compaction (read first)

**This document exists to survive context compaction.** A session resuming from it needs nothing
else except the files it points at. Do not reconstruct any of the below from memory.

**State on 2026-08-06 12:00 KST.** The line is REOPENED (see the STATUS block above for why),
and **the 5-arm roster of §12.2 is now COMPLETE**. Nothing is running, queued, or holding a GPU.
The verdict is §12.10: **outcome 3** — no arm beats the baseline, but arm C and the nonlinear twin
separate decisively and the LINEAR arm is the worse one, so on this plant the linear-evolution
constraint reaches control and costs. Paper action per the pre-registered §12.5 rule is a methods
subsection as a controlled negative, never a primary contribution.

| Step | State |
|:---|:---|
| §12.3 step 1 — `--save-action` instrument + instrumented eval | **DONE**, commits `611e5c4` + `8ca33e0` |
| §12.3 step 2 — excitation instrument + the offline A4 fit + kill gate | **DONE 2026-08-05**, 0 GPU-h of training. Gate **does not fire**. Full result and the six readings: **§12.8**. Instrument: commit `a0daf23` |
| §12.3 step 3 — arms 3-5 (~15 GPU-h) | **DONE 2026-08-06**, verdict in **§12.10**. Tags `koopC` / `koopTwin` / `koopRand` in campaign `koopman_linearity` (its `README.md` is the result SSOT, `arms_comparison.png` the figure). Implementation `e86958e`, §12.7 settlement in §12.9 |

**Judging pitfall a future comparison in this line must not repeat**: any arm-vs-baseline eval
needs `--doraemon-dr-from <baseline>/train`, or each run is evaluated on its own learned DORAEMON
curriculum and the paired floors do not apply. See §12.10.

**Facts a compacted session will otherwise lose, in priority order:**

1. **The objective is a PAPER, and Koopman is optional to it.** Owner, 2026-08-05: the existing
   paper's contributions already stand without Koopman; Koopman is being tried because it *might*
   lift the submission to a higher-tier journal. Consequences that bind every later decision: the
   main paper must never wait on or depend on this line, and §12.5's four-outcome inclusion rule
   is what protects it. A flat null costs one limitations paragraph, nothing more.
2. **Never cite arm B as "Koopman did not work".** Arm B fitted **no operator** — it appended 7
   hand-designed observables and no `K` exists anywhere in that code path. It is a negative control
   for **dictionary-only feature engineering**, not for Koopman. A reviewer will catch the
   overclaim immediately and it is not defensible. Wiki slug:
   `arm_b_is_a_dictionary_only_control_not_a_koopman_result_it_fitte.md`.
3. **Correct the X1 wiki page before any paper text reuses it.** The page titled
   `X1 tail-split ... latent reconstruction and closed-loop dispersion are decoupled` carries a
   reading that was RETRACTED on 2026-08-04. The defensible statement is not "decoupled" but "the
   exchange rate was measured and it is poor": ΔR² +0.169 is only a 6.69 % RMSE cut, so a sub-floor
   control change was PREDICTED, not evidence of decoupling.
4. **Phase 0b data is already collected** — do not re-run it:
   `experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260805_181841/`
   4 DR levels, each with `action (7750, 64, 8)` + `policy_obs (7750, 64, 72)`. Verified bit-exact
   (§12.3 step 1).

   **Three properties of this data, measured 2026-08-05, that decide step 2's design.** The first
   two are better than assumed and the third is worse.
   - The `static` protocol does **not** hold the command at zero. It injects a scripted step
     sequence — roll and pitch stepping through ±30 deg and yaw-rate through ±0.5 rad/s, changing
     every 250 steps (5 s) — so the state distribution is a commanded step-response sweep, not
     regulation about a single point. Attitude actually spans -38.6 to +34.9 deg.
   - There are **zero terminations** across all 64 envs over the full 155 s, and no periodic reset
     is visible in the obs (checked at every 1500-step episode boundary). Transition pairs are
     therefore clean; none straddles a teleport. The fit script hard-fails if this ever changes.
   - **`u` is 96.5 % linearly predictable from `o`** (R², ridge, 200k samples, raw obs). `eval.py`
     steps the deterministic inference policy, so `u = pi(o)` exactly. The consequence is specific:
     in a fitted lifted model `z' = A z + B u`, the term `B u ≈ B C z` is absorbable into `A`, so
     **`B` is not identified** and the operator is valid only along this policy's own closed loop.
     This is what makes the excitation pass mandatory — not a narrow state region, which the
     scripted commands already avoid.
5. **The eval command that works** (both `.claude/rules/03` traps avoided — no `--output_dir`,
   checkpoint through the `train` symlink), and no obs-widening flags are needed because
   `use_integral_obs` / `use_bias_ema_obs` already default to True and rebuild E-int's 72D geometry:

   ```
   CUDA_VISIBLE_DEVICES=0 /isaac-sim/python.sh constrained_albc/analysis/eval.py static \
     --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 64 --headless \
     --checkpoint experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/train/model_4999.pt \
     --save-policy-obs --save-action
   ```

   Add `--excite-std 0.10` (commit `a0daf23`) for a system-ID pass that can identify `B`. It is
   validated: paired at all 4 levels (every `dr_*`/`fault_*` key byte-identical to the unexcited
   run, which is what the dedicated RNG generator exists for), bites at the commanded amplitude,
   kills no envs (0/64 at every level), and drops `u` R² from ~0.93 to ~0.74. The paired short
   validation passes are `eval/static_260805_190144` (0.0) and `.../static_260805_190351` (0.10),
   both carrying a `NOTE.md` — they are `--segment_duration 1.0`, so their performance metrics are
   NOT comparable to a standard eval and must never be cited as one.

6. **§12.7 is still open and blocks the arm C spec**: where the linearity is consumed. If `phi_x`
   output is merely concatenated to the policy input, `K` never acts at inference and arm C
   degenerates into "arm B with a learned basis". Settle it using step 2's fit quality, not priors.
7. **Two gaps the owner has not answered**: target journal and deadline (sets the arm C timeline,
   blocks nothing cheap), and the numeric C-vs-twin separation floor (depends on §12.7).
8. **The wider paper context is NOT in this file.** The four candidate paper stories synthesised
   from the 55 substantive wiki decisions live in the omx wiki page
   `four_candidate_paper_stories_for_the_albc_line_synthesised_from_.md`. Koopman has a place in
   only two of them (A as a negative
   control, C as a comparison arm) and none in the other two. Read it before assuming this line is
   the paper.

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

1. ~~**Phase 0b instrumentation**~~ — **DONE 2026-08-05** (commit `611e5c4`). `--save-action`
   added next to `--save-policy-obs` in `analysis/eval.py` (7 sites) plus an `_MAT_VAR_DESC`
   entry; default off, `if action_log:` guards the key, so with the flag off `array_data` is
   unchanged and both `data_<level>.npz` and `.mat` stay byte-identical (structural — the off
   path was not separately re-run).

   Instrumented pass complete on the E-int baseline (`model_4999.pt`, 64 envs, headless, no
   `--output_dir`, checkpoint via the `train` symlink):
   **`experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/eval/static_260805_181841/`**

   All 4 DR levels carry `action` `(7750, 64, 8)` paired with `policy_obs` `(7750, 64, 72)`.
   **Correctness gate passed and it was able to fail**: `norm(action, axis=-1)` reproduces the
   independently-computed `action_magnitude` with max abs error **exactly 0.0** at every level,
   which is what distinguishes the applied tensor from the z-ablation branch's `actions_normal`
   or any pre/post-processed variant. Actions are non-degenerate (std 0.171 at `none` rising to
   0.186 at `hard`). No obs-widening flags were needed: `use_integral_obs` and
   `use_bias_ema_obs` already default to True, so the rebuilt cfg reproduces E-int's 72D geometry.

   Note for the A4 fit: this is the STATIC-eval closed-loop distribution under a deterministic
   policy. Offline operator fits are identified only along directions the logging policy excited,
   so the scripted-excitation pass in step 2 is load-bearing, not optional.
2. ~~**Offline A4 study**~~ — **DONE 2026-08-05**, see §12.8 for the full result. Fit `phi_x` + `K`
   on the collected rollouts plus a scripted-excitation pass; sweep latent `m`; read the
   prediction plateau, per-dim variance floor, and effective rank.
   **Kill gate:** if the learned lift's multi-step prediction error is not separable from the
   random-expansion control offline, stop here — arms 3–5 are not worth 15 GPU-h.
   **Gate outcome: DOES NOT FIRE.** The learned lift separates from the random expansion in all
   10 measured configurations, same sign every time, 2.6–20.5 sigma. The gate was able to fail —
   the random expansion is itself indistinguishable from no lift at all (§12.8), which is what a
   dead instrument would have looked like. But the gate tested separability, not size, and the
   size is the reason step 3 is still not obviously worth buying: see §12.8's decision.
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

### 12.8 Step 2 result (2026-08-05) — the offline study, and what it decides

**Zero GPU-hours of training were spent.** Everything below comes from the Phase 0b rollouts plus
two short instrument-validation passes. Artifacts: `step2_fit_lift.py` (the fit),
`step2_fit/fit_{none,hard}.json` (full-length sweep, widths 0/16/32/64/128, 3 seeds),
`step2_fit/excite_{base_short,excited}_{none,hard}.json` (excited-vs-paired-unexcited refit).

**What was fitted.** `phi(o) = [o ; psi(o)]` with the raw observation always inside the lift, so
predicting `o` is the same linear readout (first 72 rows) for every model — no decoder, and the
"shrink the latent to shrink the loss" degenerate solution buys nothing. Multi-step rollout applies
the operator repeatedly (`z <- A z + B u`) with the true logged action and **without re-lifting**;
re-lifting each step would make every model a nonlinear predictor and would not test linearity at
all. All models share one objective, optimizer and budget, differing only in what is learnable.
Train/test split is by ENV (48/16), so the test set is held-out plants wherever DR is on.

**Four model classes.** `raw` (no lift, linear operator) / `random` (frozen random lift, linear
operator — the offline stand-in for arm 5) / `learned` (learned lift, linear operator — arm 3) /
`nested_nl` (same learned lift, operator gains a residual MLP initialised to zero). The last one
**nests** the linear model rather than replacing `K` with a same-size MLP as arm 4 specifies. That
is deliberate: a nested comparison cannot be confounded by one architecture merely optimizing more
easily, so "does relaxing linearity help" gets a clean answer. It is not a substitute for arm 4.

**Measured, width 64 (the plateau), H25 = 0.5 s ahead, 3 seeds:**

| Protocol | Level | `u` R^2 | learned beats random | dropping linearity buys |
|:---|:---|---:|---:|---:|
| full 5 s segments, unexcited | none | 0.971 | +11.0 % (2.8 sigma) | +40.7 % (8.6 sigma) |
| full 5 s segments, unexcited | hard | 0.953 | **+1.6 % (2.6 sigma)** | +4.1 % (4.6 sigma) |
| short 1 s segments, unexcited | none | 0.943 | +17.6 % (8.1 sigma) | +39.3 % (31.9 sigma) |
| short 1 s segments, unexcited | hard | 0.928 | +14.2 % (7.1 sigma) | +25.8 % (16.3 sigma) |
| short 1 s segments, **excited** | none | 0.740 | +11.1 % (20.5 sigma) | +16.2 % (28.8 sigma) |
| short 1 s segments, **excited** | hard | 0.753 | +9.5 % (12.0 sigma) | +11.7 % (13.3 sigma) |

Percentages are RMSE reductions in standardized observation units; sigma is against the 3-seed
spread. Absolute errors are NOT comparable across protocol rows — the 1 s protocol changes the
command five times as often, so it is far more transient-rich and every model does relatively more
work. Compare within a row.

**Six readings, in decreasing order of how much they should change anyone's mind.**

1. **The linear constraint is never free.** Relaxing it helps in 10 of 10 configurations,
   4.6–31.9 sigma, and it survives excitation (39.3 % -> 16.2 % at `none`, 25.8 % -> 11.7 % at
   `hard`). The shrinkage under excitation is itself informative: part of the apparent nonlinear
   advantage on unexcited data was the model exploiting the confounded closed loop, and part was
   real. **Pre-registered prediction 2 in §12.4 — "arm C and the nonlinear twin do not separate
   past a decision floor" — is refuted at the PREDICTION level**, for 0 GPU-h. Whether it survives
   at the CONTROL level is exactly what arms 3–5 would buy, and the whole §12.1 framing says the
   isolation is the contribution regardless of sign.
2. **The random expansion is inert, so the learned dictionary is doing real work.** At `none`
   full-length the random lift scores 0.4651 / 0.4624 / 0.4632 / 0.4685 at widths 16/32/64/128
   against 0.4680 with no lift at all — every one inside the seed spread. Width alone buys
   nothing; only a *learned* dictionary moves the number. This is also what makes the kill gate a
   real gate: a dead pipeline would have shown the learned lift landing in that same band.
3. **The binding error term is plant generalization, not model class.** At `hard` full-length the
   train/test gap is +0.58 to +0.62 against a test error of 0.85–0.90 — roughly two thirds of the
   error is failure to transfer to held-out plants, and it is nearly identical for every model
   class including no-lift. The entire model family spans ~6 % while the gap spans ~65 %. Lifting
   does not touch the dominant term. (The `nested_nl` model has the *largest* gap at `hard`, so its
   extra capacity partly buys train accuracy that does not transfer.)
4. **The size of the win is below what this project has already priced as control-irrelevant —
   in the realistic condition.** In the full-length `hard` row, the closest thing here to normal
   operation, learned-beats-random is **1.6 %** RMSE. The X1 tail-split measured that a **6.69 %**
   RMSE improvement in latent quality produced a sub-floor (zero) control change. So the offline
   signal in the realistic condition is about 4x smaller than one already demonstrated to move
   nothing. In transient-rich conditions it reaches 9.5–17.6 %, comparable to or above that
   threshold — but "above a level that produced nothing" is not evidence that it will produce
   something. This is the single largest argument against spending the 15 GPU-h, and it is an
   argument about arm C's CONTROL result, not about the study's value.
5. **`m` from the plateau, as §6 required: ~64 added dimensions, ~12 effective.** Learned-linear at
   `none` full-length goes 0.4288 (w=16) -> 0.4189 (32) -> 0.4122 (64) -> 0.4123 (128): flat past
   64. Participation-ratio rank of `psi` saturates at 11–12 for the learned lift no matter how wide
   it is, while the random lift's rank keeps climbing (9.3 -> 19.5). The learned dictionary
   concentrates; per-dim `psi` std also falls (0.689 -> 0.334) as width grows.
6. **A wider dictionary makes `B` LESS identifiable, not more.** `u` R^2 rises monotonically with
   lift width and with learning: 0.965 (raw) -> 0.9828 (learned, w=128) on the unexcited data. A
   richer basis explains the deterministic policy better, so more of `B u` becomes absorbable into
   `A`. Anyone fitting a Koopman-with-control model on on-policy rollouts should expect this to get
   worse exactly as they make the dictionary better.

**Caveats that bound all of the above.**
- `nested_nl` is a nested residual, not arm 4's same-size `K -> MLP` swap. It answers "does
  relaxing linearity help"; it does not report what arm 4 would score.
- Everything is fitted on rollouts of a FROZEN policy. Arm C freezes `phi_x` and `K` before RL and
  the policy then moves, so these numbers are an upper bound on what a frozen operator delivers
  during training.
- One excitation amplitude (`--excite-std 0.10`) was tested, and it only brings `u` R^2 down to
  ~0.74. Residual confounding remains; a sweep was not run.
- Effect size depends strongly on how transient-rich the command protocol is (rows 1–2 vs 3–6).
  Any single number quoted without its protocol is misleading.
- `none` is not a generalization test: 23 of 23 `dr_*` keys are constant across envs there, so its
  held-out envs differ only by disturbance realization. Read `hard` for transfer claims.

**The decision this hands to the owner.** The literal gate passes, so §12.3 step 3 is not
blocked by it — but step 3 also requires explicit approval, and the offline evidence has changed
what that approval is buying. Reading 4 says arm C is unlikely to clear the control bar (which
only strengthens pre-registered prediction 1), so under §12.5 the likely landing zones are outcome
4 (flat -> "do not include as a contribution", one limitations paragraph) or outcome 3 (C and twin
separate but neither beats baseline -> a methods subsection). That is a modest return on 15 GPU-h
for a venue-tier upgrade. Against that, reading 1 is already a controlled negative at the modeling
level obtained for free, and §12.1 argued the isolation is the contribution — so a defensible
alternative is to write up the offline study and not run arms 3–5 at all. **Not decided here.**


### 12.9 Step 3 launched (2026-08-05) — the three arms, and what settling §12.7 cost

**Owner approved step 3 on 2026-08-05** ("일단 이 머신에서 koopman 말고 더 할거 없잖아... 한번
실험 돌려보자"), with the DGX flagship occupying the other machine. §12.8's argument that the
expected return is small stands and was put to the owner before this; the decision was to run.

Campaign: `experiments/rsl_rl/albc_trpo_teacher/koopman_linearity/` (DESIGN.md holds the
pre-registration). A separate campaign from `koopman_marine_obs` because that one's DESIGN
scopes itself to arm B and to a different question; arm B stays the cited low anchor.
Implementation commit `e86958e`. Protocol matches arm B: 4096 envs, 5000 iters, seed 30, from
scratch, GPU0, sequential — same device for all three, which the paired floors require.

**§12.7 is SETTLED, and not at its default.** The default was to feed the one-step prediction
`K phi_x(o_t)`. Step 2 refutes it directly: at H1 every model sits at the persistence null
(0.185-0.211 vs 0.1905), so the one-step prediction IS the current observation, and feeding it
would widen the policy input with duplicates — the exact shape of arm B's failure. Swept
`h` in {1, 5, 10, 25, 50} x {action held, autonomous} on the metric that decides it (the five
channels the policy actually receives, against the persistence null):

| h | action held | autonomous |
|--:|--:|--:|
| 1 | 23.9 % | 7.3 % |
| 5 | 31.2 % | 30.4 % |
| 10 | **36.2 %** | 35.7 % |
| 25 | 35.4 % | 36.0 % |
| 50 | 34.9 % | 36.1 % |

Chosen: **h = 25 with a zero-order hold on the action**. It is on the plateau (within 0.8 pp of
the peak), it is the horizon every §12.8 number was measured at so the offline study and the
arms speak about the same object, and the hold keeps `B` in the loop so the operator stays a
control model as the policy drifts during RL rather than being tied to E-int's frozen closed
loop. Holding the action only matters at `h=1` (23.9 % vs 7.3 %); from `h=5` on the two are
within a point of each other. The choice was made on held-out data across a flat plateau, so
selection pressure is negligible — but it was made on test data, and that is stated rather than
buried.

**What the arms hand the policy.** Five channels, `[roll, pitch, p, q, r]` predicted 0.5 s
ahead, in raw observation units, appended last (72 -> 77). Five so the widening is comparable to
arm B's seven and the "does widening alone cost transients" effect stays legible. Fed from the
PREVIOUS step's already-noised observation, arm B's rule, so the module adds a representation and
not a second independently-noisy measurement the policy could average into a denoised attitude.

**Two verifications that could have failed and did not.** The three modules hand the policy
genuinely DIFFERENT channels — pairwise relative L2 difference 0.345-0.448 across 22 560
held-out real observations, with the body-rate channels correlating only 0.55-0.77; had they
been near-identical the three runs would have been one experiment run three times. And none of
them merely echoes the current observation (relative L2 from `o_t`: 0.76-0.81), which is what
§12.7's rejection of the one-step form was about.

**Four defects the gates caught before any GPU-hour was spent**, recorded because each would
have produced plausible numbers from a wrong module:
1. The union-of-levels env split was level-major, so a flat cut put the ENTIRE `hard` level in
   the test set; the linear arms then scored worse than the persistence null. Caught only
   because the null was reported alongside the RMSE.
2. The evaluator's 2000 random windows made the persistence null NON-MONOTONIC in the horizon
   (0.36, 1.95, 0.93, 1.41) — physically impossible. Rare windows straddling a 250-step command
   change dominated it. Replaced with a dense deterministic grid.
3. The h-step ZOH map was folded into two constant matrices for the linear arms — exact in exact
   arithmetic, but Isaac Lab enables TF32, under which folded and iterated differ by 1.5e-2
   sigma (measured: 5.96e-6 with TF32 off). On the attitude channel that is 0.19 deg, above the
   0.1 deg floor. The fold was dropped; every arm iterates, which also removes an asymmetry
   between the linear and MLP arms.
4. The probe outputs saved for the load-time gate were computed from RAW observations passed to
   a function expecting STANDARDIZED ones — a 4.8 sigma disagreement with the deployed path,
   caught by that gate on the first real launch.

One earlier reading is corrected here: the claim that the ZOH assumption at `h=25` was itself
the problem came from reasoning about `||B||=4.87` being integrated 25 times, and the numbers
that appeared to confirm it were produced by the broken evaluator in defect 2. With the dense
evaluator, `h=25` ZOH is fine (roll 2.296 deg against a 3.352 deg null).

**Plant parity was verified from a recorded launch, not from reading code** — `--fault` is
required, `fault.enable` is `False` by default, and a run without it trains a different plant
(this is what voided `trpo_obs76_s30_260803_233239`). See DESIGN.md §5 for the full residual.

### 12.10 Step 3 VERDICT (2026-08-06) — outcome 3: the linear constraint costs control

All three arms ran to 5000 iterations and were evaluated paired. Full record and the figure:
`experiments/rsl_rl/albc_trpo_teacher/koopman_linearity/{README.md, arms_comparison.png}`.

**Gates first.** Survival 100 % for every arm at every DR level, so nothing below is
survivorship-biased. Pairing 96/96 against the baseline AND 96/96 arm-to-arm. That pairing was
not free: `--doraemon-dr` defaults to auto-loading each run's OWN learned curriculum, which makes
soft/medium/hard a different test distribution per arm (3/24 keys matched) and voids floors whose
own protocol string declares them "screening n=1 **paired** same-machine". `--doraemon-dr-from`
exists for exactly this and is required for any arm-vs-baseline comparison in this line.

**Result.** No arm beats the baseline — worse in 58/72 cells (arm C), 57/72 (random), 55/72
(twin), against 40/72 for arm B. But **arm C and the twin separate decisively, and the LINEAR arm
is the worse one**: arm C is worse than the twin in 51/72 cells with 15 floor crossings, including
`att_norm` `ss_error` at soft/medium/hard (+0.233 / +0.410 / +0.554 deg against a 0.1 floor) and
`ss_error_std` at medium/hard (+0.799 / +1.908 against 0.6).

| `att_norm` ss_error (deg) | none | soft | medium | hard |
|:--|--:|--:|--:|--:|
| baseline | 0.500 | 0.477 | 0.467 | 1.012 |
| arm B | 0.545 | 0.531 | 0.567 | 0.802 |
| **arm C (linear)** | **0.843** | **0.830** | **1.018** | **1.551** |
| twin (nonlinear op) | 0.626 | 0.597 | 0.608 | 0.996 |
| random lift | 0.567 | 0.464 | 0.443 | 1.635 |

Two controls do their job. The separation is **not** a prediction-quality artefact: on the five
channels the policy receives, the two modules score 39.4 % (C) and 39.5 % (twin) against the
persistence null, indistinguishable, while their outputs correlate only 0.60-0.99 per channel —
the channels differ in content, not accuracy. And it is **not** the cost of widening the
observation: C and the twin widen it identically, and arm B widens it more while regressing less.

**§12.5 verdict: outcome 3** — neither beats baseline, C and the twin separate. Paper action per
the pre-registered rule is a methods subsection as a controlled negative, not a primary
contribution, and the main paper does not wait on it. The finding is sharper than outcome 3's
wording: on this plant the linear-evolution constraint does reach control, and it costs. That is
the same direction §12.8 measured offline (relaxing linearity improved multi-step prediction in
10 of 10 configurations), now confirmed in closed loop.

Pre-registered prediction 1 (arm C does not clear the control bar) **CONFIRMED**. Prediction 2
(C and the twin do not separate) **REFUTED**, at the control level as well as the prediction level.

**Bounds.** n = 1 per arm, single seed, screening floors; the direction is consistent across
levels and metrics but no arm has a replicate. The twin is the CONTROL, not a Koopman arm — it is
also worse than baseline, so "nonlinear is better" means the linear constraint costs, not that
this stack should adopt the twin. The random-lift arm is a distinct shape rather than uniformly
worse: it matches or beats the baseline at soft/medium and collapses at hard (across-env
dispersion 7.375 deg vs 2.378), which is its own finding about expansion without structure.

**The 5-arm roster of §12.2 is now COMPLETE.** Nothing in this line is queued or running.
