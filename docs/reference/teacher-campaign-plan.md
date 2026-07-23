# Teacher Campaign — Consolidated Plan and Status (SSOT)

> Consolidated 2026-07-23 from 60 scattered `.sp/plans/` documents, 2 handoff directories,
> 3 omx campaign stores, 36 run reports, and the 16-lead wiki backlog. This document plus
> `omx campaign-status` is the authoritative answer to "what is done and what is left".
> Every legacy identifier resolves through the mapping table in section 3.
> Machine-readable state: `.omx/campaigns/<group>/` (one campaign per run group).
> Results SSOT remains the experiments tree; this document never restates report numbers
> without citing the report that owns them.

## 0. One-minute status (2026-07-23)

- **Done**: Stage 0 decision sprint (7 of 10 items), Stage A mechanism probes A1-A5
  (all DISCARD/NULL — **zero adopted config changes**), plant fix B0a (hull volume
  0.009 -> 0.00790, marinelab `7d45c2c`), corrected-plant anchor B1a (3 seeds),
  B0a-eval chain (3 old policies re-evaluated on the new plant), seed-floor measurement
  (74.8% p2p old plant, 56.0% corrected plant), DGX scale probe Arm N (NULL, lead closed),
  ablation-arm registration + smoke C0 (`509ba86`).
- **The anchor is SOUND** (retraction of the 2026-07-23 mid-session claim stands:
  retrain delta +0.110 deg = 9.6% of one obs-noise sigma, sub-threshold; plant fix is
  the win: -3.93 deg roll overshoot). Final config = the anchor config unless B0c adopts.
- **Next**: W0 zero-GPU residuals -> B0c (max_thrust DR band, paired-seed, ~15 h)
  -> D3 verdict -> C3 comparison set (4 arms x 3 seeds, ~60 h, workstation GPU0 serial)
  -> C4 deployment pack for the final teacher.
- **GPU-hours remaining on the critical path**: ~75 h workstation-serial
  (+15 h only if B0c adopts; +22.5 h optional DGX anchor replication, human-gated).
- **Blocked on hardware/human**: TAM vertical rewrite (m4 fault), IMU 45 deg (robot
  bring-up), TAM moment-arm DR band (no source), thruster T200 curve (bench), Stonefish
  P1/P2 (separate machine), cuDNN image fix (human-gated), DGX plant-fix replication
  (manual 1-line), joint1 Stage-2 (needs a new checkpoint), control_decimation ambiguity
  (robot bring-up).

## 1. Goal chain

Finish Stage B on the corrected plant -> fix the final teacher config -> build the
comparison set (paired-seed, one machine) -> distill + export the deployment pack ->
Stonefish / real-robot deployment, with the proposed method compared against the four
ablation arms. Training launches, `main` merges and `git push` remain human-gated;
eval is not. Cross-run verdicts are read at the `none` DR level only.

## 2. Storage convention (decided here; do not re-scatter)

The 2026-07-23 failure ("what is done?" unanswerable across four turns) came from plans
living in gitignored scratch with no index. From now on, one rule per artifact kind:

| Artifact | Home | Rule |
|:--|:--|:--|
| Durable campaign plan (this doc) | `docs/reference/teacher-campaign-plan.md` | the ONLY durable plan location; update in place |
| Machine campaign state | `.omx/campaigns/<group>/` | one campaign per run group; ledger appended at launch/eval/verdict time, never batch-reconstructed again |
| Experiment backlog | omx wiki `--status` fields | leads open/close in the wiki, nowhere else |
| Working scaffolding | `/workspace/.sp/plans/` | disposable; trash it the moment its conclusion lands in this doc / code / wiki |
| Results | `experiments/.../<run_id>/analysis/*/report.md` | unchanged SSOT |

**Location decision, with reason**: `.sp/` and `experiments/` are both gitignored
(verified: `git ls-files experiments/` is empty), so neither can hold a plan that must
survive and be trusted. `docs/reference/` is versioned with code and indexed by
`docs/README.md`; a campaign plan is lookup material (Diátaxis reference). Hence this file.

**Multi-group campaign decision, with reason**: the omx campaign store derives
`runs[]` and `derived_status` from group-keyed ledger events, so a single umbrella
campaign whose id matches no run group would show zero runs forever — recreating the
exact abandoned-ledger failure this consolidation fixes. Therefore: **one campaign per
run group**, each carrying `program: "teacher-final-closeout"` and a `predecessor`
pointer in its `plan.json`; the cross-group program view is this document.

## 3. Canonical id scheme and legacy mapping

**Canonical scheme** (adopted from the dominant existing structure, per the
"adopt, don't rename" rule): stage letter + number, as defined by the 2026-07-20
campaign document — `Z1..Z10` (Stage 0, zero-GPU), `A1..A7` (Stage A, mechanism probes),
`B0a..B3` (Stage B, plant refresh), decision gates `D0/D0.5/D1/D2/D3` — extended with
`C0/C3/C4` from the 2026-07-22 roster for its three genuinely-new blocks, and one
insertion `B1a-dgx` (queued DGX anchor replication). Measurement campaigns are
identified by their run-group name (`seed_floor_dgx`). Stable under insertion (ids are
never renumbered), legible without the document (stage letter carries meaning),
distinct from run ids (`make_run_id` output) and proposal ids (`next-YYYYMMDD-HHMMSS`).

**All legacy names are retired.** The table below exists only so old documents and
wiki pages remain readable.

| Legacy id | Canonical | Introduced by |
|:--|:--|:--|
| Z1..Z10 | Z1..Z10 (canonical) | `.sp/plans/2026-07-20-final-teacher-batch-campaign.md` |
| A1..A7 | A1..A7 (canonical) | same |
| B0a, B1a, B0b, B1b, B0c, B1c, B1d, B2, B3 | canonical | same |
| D0, D0.5, D1, D2, D3 | canonical gates | same |
| C0 | C0 (canonical) | `.sp/plans/2026-07-22-final-model-and-comparison-roster.md` |
| C1 | alias -> B1a (3-seed anchor) + Phase-2 paired-seed tuning (now: B0c) | same |
| C2 | alias -> B2 | same |
| C3, C4 | C3, C4 (canonical) | same |
| "Phase 0/1/2/3" (machine-split) | Phase 0 -> W0 set; Phase 1 -> B0a+B1a; Phase 2 -> paired-seed tuning (B0c, deferred A6); Phase 3 -> B2 | `.sp/plans/2026-07-22-batch-pass-and-machine-split.md` |
| "Phase 1", "Phase 2" (conversation) | = batch-pass Phase 1 / Phase 2 above | conversation 2026-07-22/23 |
| ITEM 1 | run `trpo_biasema_extend8k_260716_162849` (budget extension; discarded) | `.sp/plans/2026-07-15-wiki-backlog-experiment-program.md` section 1b |
| ITEM 2 | shared-exam re-eval (`next-20260716-144615`; done) | same |
| P-A1..P-A9, P-B1..P-B7, P-C1..P-C6, P-D1..P-D5, E1..E10 (hw), P-F1 | 2026-07-15 program tracks. Executed: P-B1 = run `trpo_biasema_260715_142543` (ADOPTED, `f42a67f`); P-A8 = run `trpo_perflb200-moreiters_260715_195227`; P-B7 = ss-error brief (candidates 1-3 deferred, 4 dead, 5 done as ITEM 2). All others resolve to wiki-slug backlog rows (section 6) | `.sp/plans/2026-07-15-wiki-backlog-experiment-program.md` |
| e1, e2, e3, e4 (lowercase) | runs `trpo_e1_latdr / e2_biasobs / e3_extend10k / e4_xyprune` in `teacher_baseline_opt` (pre-TAM; VOID as absolute results, differential conclusions only) | p7_tail campaign, 2026-07-13 |
| "e3 scale-up", Arm N, Arm I | group `e3_dgxscale_buoyfix`. Arm N = run `trpo_e3scaleN_envs8192_260722_151230` (ran, NULL). Arm I = cancelled 2026-07-23 (never ran) | `.sp/plans/2026-07-22-DGX-handoff-e3-scaleup.md` |
| Exp A, Exp B | Exp A -> e4/xyprune lineage (dead, DISCARD + user rejection); Exp B -> folded into the 28D union p_t (2026-07-12) | `.sp/plans/2026-07-08-dr-offset-prune-buoy-split-design.md` |
| R1..R6 (sigma-gate) | R1 = decouple `integral_gate_threshold` (NOT in code — the 2026-07-20 operating brief's "Z8 shipped" claim is refuted by grep at HEAD `03c854c`); R6 = A6. Both deferred | `.sp/plans/REVIEW_reward_sigma_integral_gate.md` |
| R1..R6 (bias-reward — a DIFFERENT R-set) | bias-R1 (expose `_bias_ema` as obs) became P-B1 = biasema = ADOPTED; bias-R3 = carry-over reset (deferred, unimplemented); others unscheduled | `.sp/plans/REVIEW_bias_reward_theory.md` |
| Group A, Group B, Group C, Group D | 2026-06-29 sim-to-real audit groups. Group A control-timing (`control_decimation` 1->5) is OPEN-AMBIGUOUS (still 1 in code); Group B (priv-obs bounds) landed; Group C (constraint over-spec) TBD; Group D (measurability sweep) done | `.sp/plans/2026-06-29-sim-to-real-audit-before-baseline-retrain.md` |
| E1..E4 (uppercase, legacy) | `dr_harder` campaign runs (2026-06, `experiments/legacy/`) — distinct from lowercase e1..e4 | legacy dr_harder campaign |
| M1..M3, N1..N5, P1..P7, options (a)/(b)/(c) | 2026-07-12 workspace-consolidation internals (completed; not experiment ids) | `.sp/plans/2026-07-12-workspace-consolidation-and-baseline-prep.md` |
| Task 1..N, A1-A6 (omx-soak), A1-A6 (omstar audit), X1-X3, C1-C3/B1-B4 (wiki-family) | per-document TDD/harness item numbering, NOT experiment ids — excluded from this scheme | various |

## 4. Disk-derived status (never from a document's claim)

Evidence rules: train = numeric-sorted final `model_N.pt`; eval = `eval/static_<ts>/`;
verdict = the run's latest `analysis/*/report.md`. All 22 runs verified on disk
2026-07-23; all `train` symlinks resolve; `omx tree-audit` ok (0 errors).

### Stage 0 (zero-GPU)

| id | what | status | evidence |
|:--|:--|:--|:--|
| Z1 | per-dim log_std floor read | DONE 2026-07-21: 5/8 dims floored, free = {arm1, thr0, thr3} | wiki `april_2026_entropy_collapse...` |
| Z2 | curriculum state check | DONE 2026-07-21: 5k runs never saturate (anchor Beta a 12.900 -> 1.670, 0/20 box-bound); 8k@si250 saturates at iter ~7000 | wiki `curriculum_recalibration...`; reports `diagnose-20260723-134359`, `diagnose-20260720-124259` |
| Z3 | encoder z_sweep on adopted checkpoint | NOT EVIDENCED — no sweep artifact on disk for the biasema/anchor checkpoints | find over experiments tree |
| Z4 | delay-sweep eval instrument | NOT DONE — `dr_config.py`/`eval.py` have zero `control_delay` references | wiki latency page (re-verified at HEAD 2026-07-20) |
| Z5 | Stonefish P1/P2 pre-checks | NOT DONE (separate machine) | wiki `stonefish_yaw_gap...` |
| Z6 | physical-span sourcing | PARTIAL: max_thrust ±15% SOURCED; TAM moment-arm NO SOURCE (cannot-close); battery-voltage memo residual | wiki `sim_hydro_nominal...` |
| Z7 | hull F_bu decision | DONE 2026-07-22: volume-only fix, applied as B0a | marinelab `7d45c2c`; wiki commit `29bcbea` |
| Z8 | R1 `integral_gate_threshold` | NOT DONE (grep-verified absent at HEAD; operating-brief claim refuted) | `grep -rn integral_gate_threshold` = 0 hits |
| Z9 | pick A7 probe | MOOT — A7 dropped 2026-07-21 | operating brief section 3 |
| Z10 | penalty-rescale gate | DECIDED BY GATE: no measured deficiency; four penalties ≈ 1.4% of total reward (-0.12 vs ~8.8) -> lead closes resolved-by-gate | report `diagnose-20260723-134359`; wiki `penalty_vs_objective...` |

### Stage A (group `teacher_baseline_posttam`) — 5/5 run, zero adoptions

| id | run | train/eval | verdict | adopted |
|:--|:--|:--|:--|:--|
| A1 | `trpo_stepint400_260720_180208` | model_7999 / static_260721_014808 | H1 REFUTED (iterations dominate the roll transient; DR box is protective) — DISCARD | no |
| A2 | `trpo_entcoefzero_260721_014731` | model_4999 / static_260721_064204 | diagnostic: entropy BONUS (not IPO barrier) holds sigma; eval worse at hard | no (diagnostic) |
| A3 | `trpo_minstdthr008_260721_064149` | model_4999 / static_260721_113503 | PRIMARY FAIL (`os_env_mean` +26.2% vs required -10%) — DISCARD | no |
| A4 | `trpo_privslim24d_260721_114717` | model_4999 / static_260721_180055 | FAIL all clauses; lin_vel is load-bearing (ablation, not dedup); keep 28D | no |
| A5 | `trpo_budgetslack_260721_181133` | model_4999 / static_260721_230512 | NULL after seed-floor resolution (deltas within seed noise); inert constraints confirmed inert | no |
| A6 | (= sigma-R6) | NOT RUN | deferred (section 5) | — |
| A7 | — | DROPPED 2026-07-21 (replaced by A6 slot) | — | — |

Reports: `diagnose-20260721-020253 / -065341 / -164331 / -190151 / diagnose-20260722-103723`.
Pre-Stage-A posttam runs (baseline, perflb200, perflb200-moreiters, biasema, extend8k):
biasema ADOPTED (`use_bias_ema_obs=True`, `f42a67f`); lb=200 NOT adopted; both 8k
extensions net-negative. See group ledger.

### Stage B + measurement campaigns

| id | run(s) | status | evidence |
|:--|:--|:--|:--|
| B0a | marinelab `7d45c2c` (volume 0.009 -> 0.00790) | DONE 2026-07-22; wiki apply-gate closed | commit; wiki `29bcbea` |
| B0a-eval | `trpo_dgxseed30/31/32` re-evaluated on new plant | DONE 3/3 (`static_260723_110214/111102/111955`) | eval dirs |
| B1a | `trpo_buoyanchor_s30/s31/s32_26072{2,3}_*` | DONE 3/3 trained + evaluated; s30 analyzed: plant fix ADOPT (-3.93 deg roll overshoot), retrain delta +0.110 deg = 9.6% of 1 sigma (sub-threshold) -> **anchor SOUND** | report `diagnose-20260723-134359` |
| seed_floor_dgx | `trpo_dgxseed30/31/32_260721_*` | DONE: seed floor 74.8% p2p (old plant), 56.0% p2p (corrected, from B1a 3 seeds) — kills every single-seed ±5% verdict | same report, lines 60-65 |
| B1a-dgx | queued `trpo_buoyanchordgx_s30_PLACEHOLDER` | PENDING human approval; stakes revised DOWN (discriminates a sub-threshold effect); OPTIONAL — C3 does not depend on it | proposal `next-20260723-dgxanchor` |
| B0b/B1b | — | NOT RUN — re-judged, deferred with edge (section 5) | — |
| B0c/B1c | — | NOT RUN — KEEP, next tuning arm (section 5) | — |
| B1d | — | conditional on Z4; deferred with latency lead | — |
| B2 | Arm N = `trpo_e3scaleN_envs8192_260722_151230` | envs-only half ran: NULL (all metrics inside the 3-seed anchor band; 9.65 s/iter, 13.41 h). Arm I cancelled. Lead closed 2026-07-23 | report `diagnose-20260723-134359`; wiki e3 page |
| B3 | — | NOT RUN — blocked (needs a station-keeping checkpoint on unlimited joint1 physics) | wiki `joint1_stage_1_gate...` |

### Comparison / deployment track

| id | status | evidence |
|:--|:--|:--|
| C0 | DONE 2026-07-23: 4 arms registered (`509ba86`), PPO-Enc dim-sync fixed shared (`_core/runners/__init__.py`), smoke x2 per arm passed (artifacts preserved in `/workspace/.trash/smoke-ablation-reg-260723/`). RESIDUAL: C0.4 (eval.py reads one smoke ckpt per arm) and C0.5 (arm-identity audit: obs wiring / `class_name` / `num_constraints` vs the ladder) not evidenced -> W0 items | git log; CHANGELOG 2026-07-23; task-reference.md |
| C3 | NOT RUN — the largest remaining block: 4 arms x 3 seeds (30/31/32, paired with the anchor), workstation GPU0 serial, ~60 h. Proposed arm = the three B1a anchor runs themselves while final config == anchor config | roster section; budget section 8 |
| C4 | PARTIAL: s30 student distilled (`trpo_buoyfix_s30_tcn_260722_184307/184632`) under the cuDNN-disabled slow path; full C4 = per-FINAL-teacher distillation + `export_deploy.py --golden` pack + C4a latent-collapse diagnostic | student tree; wiki cudnn page |

## 5. Re-judgment of every remaining item (KEEP / DROP / MODIFY / ADD)

| item | verdict | deciding evidence |
|:--|:--|:--|
| B0b/B1b curriculum recalibration TRIPLE | **MODIFY -> deferred with reactivation edge**. Budget-conditional: at the adopted 5000-iter budget the curriculum is iteration-limited, not bounds-limited (anchor Beta a 12.900 -> 1.670, 0/20 box-bound at 4750) so widening is inert; at 8k+ the box saturates (iter ~7000) and widening becomes the only lever. No 8k+ run remains on the roster (extensions rejected twice, Arm I cancelled) -> B0b fires ONLY if an 8k+ regime is ever re-rostered, and must then precede it | `diagnose-20260723-134359` (Beta table), `diagnose-20260720-124259` (saturation), wiki Z2 |
| B0c/B1c max_thrust DR band | **KEEP, re-parented onto B1a config** (B1b no longer exists ahead of it). One variable, band SOURCED (±15%). Paired-seed: 3 runs vs the 3 anchor seeds, ~15 h. Runs BEFORE C3 because adoption changes the final config. Residual: battery-voltage window memo (Z6). TAM-arm band stays excluded (no source) | wiki `sim_hydro_nominal...`; seed-floor methodology |
| B1d latency arm | **DROP as scheduled item; deferred with edge** — Z4 instrument does not exist and delay is off-DORAEMON (stalls the curriculum, e1 lesson). Edge: build Z4, then re-propose. User direction (latency wanted in final training config, 2026-07-20) recorded, not actionable yet | wiki latency page (both blockers re-verified) |
| B2 scale-up | **DROP**. Arm N (envs x2 at 5k) NULL; iteration extension answered net-negative twice (extend8k, moreiters); Arm I cancelled as a third dose of the same lever. The campaign's literal question ("scale after the box is widened") is moot while B0b is deferred — reactivation edge shared with B0b | wiki e3 page (closed 2026-07-23); reports |
| B3 joint1 Stage-2 | **DEFER** (unchanged): requires a station-keeping-on-unlimited-physics checkpoint that does not exist; not on the final-model path | wiki joint1 page |
| B1a-dgx replication | **KEEP as OPTIONAL, human-gated** — already queued; stakes low (discriminates a 9.6%-of-sigma effect); C3 does not wait for it | proposal `next-20260723-dgxanchor` |
| A6 (sigma-R6) + Z8 (sigma-R1) | **DEFER both** — R1 is not in code (grep-verified; the "Z8 shipped" record was wrong) and nothing on the roster consumes it now that R6 is deferred; zero adopted levers + 56% seed floor make another ±5% tuning probe paired-seed-expensive with no motivating deficiency. Edge: a future reward-kernel experiment (R1 must land first, behavior-preserving) | grep; wiki reward_sigma page |
| Z10 penalty rescale | **DROP — close resolved-by-gate**: the page's own gate (measured deficiency) answers itself; penalties are 1.4% of reward | report; wiki page |
| Z3 encoder sweep | **KEEP (W0)** — zero-GPU rule-03 hygiene on the anchor checkpoint | rule 03 |
| C0 residuals (C0.4, C0.5) | **KEEP (W0)** — cheap; a mislabelled arm invalidates the comparison it anchors | roster C0 items 4-5 |
| C3 comparison set | **KEEP** — machine decided: **workstation** (e3 NULL means the final model is the workstation Stage-B model; the plant fix lives only on the workstation editable install). 12 runs paired-seed | roster section 3 ordering argument; batch-pass DGX wrinkle |
| C4 deployment | **KEEP** — per-final-teacher distillation + golden pack. Recommend the cuDNN cu12 image fix first (human-gated): collapses ~5 h/pack back to minutes. Includes **C4a** (ADD): closed-loop latent-collapse diagnostic re-pointed at the buoyfix student (one eval, no training) | wiki cudnn + latent-collapse pages |

**ADD rows (findings nobody rostered — now recorded, all deferred with owners/edges):**

| item | disposition |
|:--|:--|
| `control_decimation` 1 -> 5 (audit Group A) | OPEN-AMBIGUOUS since 2026-06-29; still 1 in code; wiki ledger marks it AMBIGUOUS. NOT applied to this campaign (applying would invalidate the anchor). Resolve at robot bring-up; until then the anchor is recorded as pre-control-decimation alongside the other pre-item caveats |
| carry-over reset A/B (bias-R3) | designed, never implemented (`reset_error_state_on_resample` absent from code); harm unproven; defer — optional rider on any future from-scratch retrain |
| actuation-noise experiment | infrastructure landed (`ActuationNoiseCfg`, off-by-default) but the experiment was never rostered; defer behind the same measured-deficiency gate as Z10 (deployment vibration evidence) |
| P-B7 candidates 1-3 (k_bias decouple, two-scale kernel, L1/Huber r_bias) | never re-judged after Stage A; defer — reactivation edge: measured steady-state deficiency on the deployed system |
| per-axis DORAEMON success gate; z-conditioned `state_dependent_std`; yaw-reward k5 (2026-05-28) | shadow leads D1 never elevated; state_std variant already showed a disqualifying nominal regression in the legacy campaign; defer/close — re-derive against the current plant before any revival |

## 6. Backlog reconciliation — all 16 live leads (exhaustive)

| wiki lead | disposition |
|:--|:--|
| `april_2026_entropy_collapse...` | **CLOSE (resolved)** — Item 1 closed by Z1; Item 2 answered by A2 (`trpo_entcoefzero`, report 2026-07-21). Caveat recorded: eval-side deltas are single-seed; the mechanism verdict (sigma trajectories) stands |
| `baseline_open_experiment_leads_backlog...` | **CLOSE (resolved)** — index page; every sub-lead now carried in this document or the wiki backlog; the 2026-07-20 park order is discharged by this consolidation |
| `closed_loop_latent_collapse...` | **CARRY -> C4a** (one eval on the buoyfix student; cheap, unblocked) |
| `constrainttrpo_slack_tail...` | **CLOSE (resolved)** — answered by A5 (budgets x100 on the 2 inert constraints: constraints stayed satisfied, tracking deltas within seed noise); page had already deprioritized the remainder |
| `curriculum_recalibration_protocol...` | **CARRY (partial)** — Z2 done; max_thrust half proceeds as B0c; B0b retrain arm deferred with the 8k+ reactivation edge; TAM-arm half blocked-on-source |
| `e3_s_5000_iter_budget_verdict...` | **CLOSE (resolved)** — page self-declared scope empty 2026-07-23 (Arm N NULL, Arm I cancelled); status flipped to match |
| `experiment_idea_latency...` | **DEFER** — both blockers stand (no Z4 instrument; off-DORAEMON stall). Edge: build Z4 -> baseline sweep -> only then a training probe. User direction (latency in final config) recorded |
| `joint1_stage_1_gate_go...` | **DEFER** — B3 blocked on a checkpoint that does not exist; not on the final-model path |
| `penalty_vs_objective_exchange_rate...` | **CLOSE (resolved-by-gate)** — Z10 |
| `reward_sigma_integral_obs_gate...` | **DEFER** — R1 not in code, R6 (=A6) deferred; edge = next reward-kernel experiment |
| `stonefish_yaw_gap_claim_review...` | **CARRY as deployment prerequisite (Z5)** — P1/P2 on the Stonefish machine; treat the coming Stonefish run as a diagnostic against this lead, not validation |
| `thruster_nonlinear_curve_t200...` | **DEFER** — hardware bench measurement; feature stays OFF (deliberate) |
| `container_cudnn_is_cu13...` | **CARRY as C4 infra** — human-gated image fix; only blocks distillation throughput (~70x), not teacher training |
| `imu_45deg_offset...` | **DEFER** (user 2026-07-20) — robot bring-up track; zero sim-side impact meanwhile |
| `sim_hydro_nominal...` | **SPLIT** — max_thrust -> B0c (carried); TAM moment-arm -> cannot-close (no geometric-tolerance source) |
| `tam_vertical_single_motor_dual_esc...` | **DEFER** — m4 remeasurement (HW fault) + full B1 vertical session before any config.py edit |

Count: 16/16 rows. After the five closes: 7 `needs-experiment` + 4 `needs-apply-before-retrain` remain live.

## 7. Remaining-work sequence (dependencies explicit)

```
W0 (zero-GPU, now):      C0.4 + C0.5 verification; Z3 encoder sweep; Z6 battery memo
                          (campaign registration + wiki closes: done by this consolidation)
Human decisions:          (a) fire or drop B1a-dgx (queued, optional, 22.5 h DGX)
                          (b) cuDNN cu12 image fix (recommended before C4)
                          (c) DGX plant-fix hand-replication (only needed if DGX rejoins)
B0c  (after W0):          max_thrust ±15% DR arm, paired-seed 3 runs vs anchor, ~15 h -> D3
C3   (after B0c verdict): 4 ablation arms x seeds {30,31,32}, workstation GPU0 serial, ~60 h
                          (+3 proposed-arm runs ONLY if B0c adopts)
C4   (after C3):          distill final teacher -> golden pack -> C4a latent diagnostic
                          -> Stonefish diagnostic run (Z5 framing)
```

Standing gates (unchanged): every training launch via `omx queue-launch` + human approval;
`marinelab` must stay on `exp/buoyancy-recenter` (checking out `main` silently reverts the
plant); deployment checkpoint rule pre-declared = median seed by none-level roll `ss_error`
(claim = the full paired distribution regardless of which seed ships).

## 8. GPU budget (measured, not estimated)

| resource | throughput | note |
|:--|:--|:--|
| Workstation RTX 4070 (GPU0) | 3.58 s/iter @4096 envs -> ~5.0 h per 5000-iter run | 11.3/12.3 GB at 4096 envs: comparison set is SERIAL on GPU0; the 8 GB 4060 evals |
| DGX GB10 | 5.409 s/iter @4096; 9.65 s/iter @8192 (13.41 h/run) | source build, `./isaaclab.sh -p` only; one job at a time; plant fix NOT yet replicated there |

| block | runs | wall clock |
|:--|--:|--:|
| B0c paired-seed | 3 | ~15 h |
| C3 comparison set (workstation) | 12 | ~60 h (~2.5 days serial) |
| + proposed-arm re-run iff B0c adopts | 3 | ~15 h |
| B1a-dgx (optional, human-gated) | 3 | ~22.5 h (DGX) |
| C4 distillation | per teacher | ~5 h/pack until the cuDNN image fix; minutes after |

Critical path ≈ **75 h** workstation-serial (90 h if B0c adopts), plus analysis gates.

## 9. DONE criterion and cannot-close list

**DONE** means: C3 is built paired-seed on the final config on one machine; C4 ships a
golden pack for the final teacher (with C4a run); and every remaining open lead is either
carried with a canonical id above, hardware/deployment-blocked, or explicitly
user-deprioritized with a recorded reactivation edge. Nothing is left open silently.

**Cannot-close (blocked outside this campaign)**: TAM vertical rewrite (m4 HW fault);
IMU 45 deg (robot measurement); TAM moment-arm DR band (no geometric-tolerance source);
thruster T200 curve (bench measurement); Stonefish P1/P2 (separate machine);
cuDNN image fix (human-gated); DGX plant-fix replication (human, 1 line);
joint1 Stage-2 / B3 (needs a new checkpoint); `control_decimation` ambiguity
(robot bring-up); B0b + B2 (8k+ regime reactivation edge); carry-over reset,
actuation-noise experiment, P-B7 candidates 1-3, latency/B1d+Z4, A6/R1+R6
(deferred with stated edges in sections 5-6).

## 10. Record of this consolidation

- Survey basis: 60 content documents in `.sp/plans/` (all read), 2 handoff dirs,
  3 campaign stores, 3 pending-launch artifacts, 2 proposals, 5 DESIGN/README files,
  36 reports (via `omx report-parse`), 335-page wiki with 16 live leads, CHANGELOG,
  task-reference. Known document inaccuracies found and corrected here: wiki page count
  334 (not 335); posttam plan.json holds 6 proposals (not 5); the report glob spans
  `experiments/legacy/` too; "Z8 shipped" refuted by grep.
- Retired: superseded `.sp/plans/` documents and both handoff dirs moved to
  `/workspace/.trash/sp-plans-cleanup-260723/` (recoverable). `.sp/plans/` now holds
  only live, unexecuted work instructions.
- Campaign stores registered/back-filled 2026-07-23: `teacher_baseline_buoyfix`,
  `seed_floor_dgx`, `e3_dgxscale_buoyfix` created; `teacher_baseline_posttam` ledger
  back-filled from run reports (a one-time reconstruction; from now on events are
  appended at launch/eval/verdict time).
