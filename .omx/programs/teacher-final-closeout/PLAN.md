# Teacher Campaign — Consolidated Plan and Status (SSOT)

> Consolidated 2026-07-23 from 60 scattered `.sp/plans/` documents, 2 handoff directories,
> 3 omx campaign stores, 36 run reports, and the 16-lead wiki backlog. This document plus
> `omx program-status` is the authoritative answer to "what is done and what is left".
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
  [AUDIT-CORRECTION 2026-07-23, section 11: "-3.93 deg" mislabels the unit — `os_env_mean`
  is percent-of-step (`recompute_metrics.py:109`), so the plant win is -3.93 pp =
  **-1.18 deg** on the 30-deg roll steps (24% of the settling gate, not 79%). The
  "+0.110 deg retrain delta" (C-B) is machine-confounded (B policies DGX-trained, C
  workstation-trained; section 11.2). "Anchor SOUND" stands on corrected grounds: the
  clean B-A plant shift plus the anchors' in-family absolute performance.]
- **Next** (REVISED by the 0b priority pivot, user 2026-07-23): W0 COMPLETE 2026-07-23
  (C0.4 4/4, C0.5, Z3, Z6) -> **B0c stage 1, seed 30 only, ~5 h** (proposal
  `next-20260723-175314`, lint-clean, code on `exp/max-thrust-dr` in both overlay repos)
  -> D3 verdict -> C4 deployment pack. **C3 (4-arm x 3-seed ablation) is DEFERRED to a later
  paper phase** and is no longer on the critical path.
- **GPU-hours remaining on the critical path**: ~10 h workstation-serial (B0c stage 1 + one
  C4 pack). Deferred, not deleted: C3 ~60 h at the paper phase; B0c stage 2 +10 h only if
  stage 1 clears; +15 h proposed-arm re-run only if B0c adopts.
- **Roster warning (see 0b)**: B0c is the ONLY remaining config candidate. If it returns NULL,
  the tuning roster is empty and the choice is "accept the anchor as final" or "revive a
  deferred lead with new motivation".
- **Blocked on hardware/human**: TAM vertical rewrite (m4 fault), IMU 45 deg (robot
  bring-up), TAM moment-arm DR band (no source), thruster T200 curve (bench), Stonefish
  P1/P2 (separate machine), cuDNN image fix (human-gated), DGX plant-fix replication
  (manual 1-line), joint1 Stage-2 (needs a new checkpoint), control_decimation ambiguity
  (robot bring-up).

## 0b. PRIORITY PIVOT (user decision 2026-07-23) — tuning first, paper ablation later

**Decision, in the user's words**: run only ONE seed for now; the ablation experiments the
paper needs are postponed; finding the optimal setting comes first.

What this changes:

- **C3 (4 ablation arms x 3 seeds, ~60 h) is DEFERRED to a later paper phase.** It is a
  publication artifact — it proves the method's components carry their weight — not a
  config-selection instrument. It no longer sits on the critical path.
- **All tuning work runs single-seed paired screening** (protocol 11.6 item 3), which is
  already how B0c stage 1 was staged. Paired same-seed same-machine comparison cancels the
  seed term, so single-seed screening is methodologically sound *for screening*.
- **11.6 item 5 is now SPLIT, not repealed.** The paper number is still the full 3-seed
  distribution with the pre-declared median-seed deployment rule. Single-seed screening
  results are NOT paper numbers and must never be reported as the ablation table. When the
  paper phase opens, the 3-seed set has to be run. Deferring is not cancelling.
- Timing consequence, stated plainly: this does not save the 60 h, it moves it. The only
  genuine saving is if a single-seed pass eliminates an arm before its seeds are spent.

**A fact this pivot exposes, which the user should see before committing GPU time**: after
the section-5 re-judgment, **B0c is the ONLY remaining config candidate on the roster**.
Every other tuning lever was deferred or dropped with a recorded reason (B0b/B2 behind an
8k+ reactivation edge; A6/R1 with no consumer; B1d/latency with no instrument; Z10 closed
by gate; the four ADD rows all deferred). So "find the optimal setting first" currently
means: run B0c (~5 h) and then, if it is NULL — which the 5/5 zero-adoption Stage-A record
makes the likely outcome — the tuning roster is EMPTY. At that point the options are to
accept the anchor config as final, or to revive a deferred lead with new motivation. That
is a decision to make consciously, not to discover after the fact.

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
| Durable campaign plan (this doc) | `.omx/programs/teacher-final-closeout/PLAN.md` | the ONLY durable plan location; update in place (moved 2026-07-23, see decision update below) |
| Machine campaign state | `.omx/campaigns/<group>/` | one campaign per run group; ledger appended at launch/eval/verdict time, never batch-reconstructed again |
| Experiment backlog | omx wiki `--status` fields | leads open/close in the wiki, nowhere else |
| Working scaffolding | `/workspace/.sp/plans/` | disposable; trash it the moment its conclusion lands in this doc / code / wiki |
| Results | `experiments/.../<run_id>/analysis/*/report.md` | unchanged SSOT |

**Location decision, with reason**: `.sp/` and `experiments/` are both gitignored
(verified: `git ls-files experiments/` is empty), so neither can hold a plan that must
survive and be trusted. `docs/reference/` is versioned with code and indexed by
`docs/README.md`; a campaign plan is lookup material (Diátaxis reference). Hence this file.

**Location decision UPDATE (2026-07-23, supersedes the paragraph above)**: user direction —
ALL experiment records, the plan included, belong under `.omx` (one root). omx v0.9.0
shipped the program layer (`.omx/programs/<program-id>/{PLAN.md, program.json}` plus
`omx program-status`), so this document moved VERBATIM from
`docs/reference/teacher-campaign-plan.md` to `.omx/programs/teacher-final-closeout/PLAN.md`
(a redirect stub remains at the old path for the 30+ historical references). `.omx` is
git-tracked in this repo, so the versioning/trust argument above is unchanged. The
section-0 contract is now "this PLAN.md + `omx program-status`" (cross-group machine view
aggregating the 4 member campaigns' ledgers).

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
| Z3 | encoder z_sweep on adopted checkpoint | DONE 2026-07-23: swept the anchor (`trpo_buoyanchor_s30`) and the pre-fix biasema checkpoint; no collapse in either (~7/9 latent dims active). Post-fix sensitivity shifts off Payload onto Buoy Volume / CoG-Z / CoB-Z, which is what the plant fix should do | `.../teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/train/encoder_analysis/sweep_heatmap.png`; same file under `teacher_baseline_posttam/trpo_biasema_260715_142543` |
| Z4 | delay-sweep eval instrument | NOT DONE — `dr_config.py`/`eval.py` have zero `control_delay` references | wiki latency page (re-verified at HEAD 2026-07-20) |
| Z5 | Stonefish P1/P2 pre-checks | NOT DONE (separate machine) | wiki `stonefish_yaw_gap...` |
| Z6 | physical-span sourcing | PARTIAL, residual CLOSED 2026-07-23: max_thrust ±15% SOURCED; battery window CONFIRMED 4S LiPo ~14-16.8 V — narrower than the 14-18 V source window, so the band is conservative and stays as rostered (no DR-config change); TAM moment-arm NO SOURCE (cannot-close) | wiki `sim_hydro_nominal...` (memo merged 2026-07-23) |
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
| B1a | `trpo_buoyanchor_s30/s31/s32_26072{2,3}_*` | DONE 3/3 trained + evaluated; s30 analyzed: plant fix ADOPT (-3.93 deg roll overshoot), retrain delta +0.110 deg = 9.6% of 1 sigma (sub-threshold) -> **anchor SOUND** [AUDIT-CORRECTION 2026-07-23: -3.93 pp = -1.18 deg (os unit is percent-of-step); retrain delta C-B machine-confounded — see section 11] | report `diagnose-20260723-134359`; section 11 |
| seed_floor_dgx | `trpo_dgxseed30/31/32_260721_*` | DONE: seed floor 74.8% p2p (old plant), 56.0% p2p (corrected, from B1a 3 seeds) — kills every single-seed ±5% verdict [AUDIT-SCOPE 2026-07-23: this floor is UNPAIRED (cross-seed); it does not transfer to paired same-seed same-machine deltas — section 11.4 D3] | same report, lines 60-65 |
| B1a-dgx | queued `trpo_buoyanchordgx_s30_PLACEHOLDER` | **DROPPED (user 2026-07-23)** — audit section 11: the +109% cross-machine term makes the probe non-discriminating; queue artifact marked `dropped`, campaign ledger noted. RACE, resolved 2026-07-23: the DGX session had already launched seed 30 under an earlier green light when the drop was decided here; its stand-down killed it at ~1750 iters and never launched s31/s32. A partial DGX run dir therefore exists on that machine, untransferred and not analyzable (unconverged, and cross-machine anyway) — treat any `trpo_buoyanchordgx*` artifact as dead by decision, not as data | proposal `next-20260723-dgxanchor` (status DROPPED); DGX stand-down report 2026-07-23 (relayed, not verifiable from the workstation) |
| B0b/B1b | — | NOT RUN — re-judged, deferred with edge (section 5) | — |
| B0c/B1c | — | NOT RUN — KEEP, next tuning arm (section 5) | — |
| B1d | — | conditional on Z4; deferred with latency lead | — |
| B2 | Arm N = `trpo_e3scaleN_envs8192_260722_151230` | envs-only half ran: NULL (all metrics inside the 3-seed anchor band; 9.65 s/iter, 13.41 h). Arm I cancelled. Lead closed 2026-07-23. CORRECTION 2026-07-23: "Arm I produced no artifact" (pre-audit handoff) is wrong — the DGX stand-down found `e3_dgxscale_buoyfix/trpo_e3scaleI_iters12k_260723_044049` with checkpoints up to `model_6200.pt` (52% of the 12k target) plus `logs_queue/e3scaleI_260723.log`, still on DGX and never transferred. It stays out of the campaign either way (cancelled, unconverged, DGX-trained), but it is a real 8k+-regime partial should the B0b reactivation edge ever fire — decide transfer-or-discard before wiping that machine | report `diagnose-20260723-134359`; wiki e3 page; DGX stand-down report 2026-07-23 |
| B3 | — | NOT RUN — blocked (needs a station-keeping checkpoint on unlimited joint1 physics) | wiki `joint1_stage_1_gate...` |

### Comparison / deployment track

| id | status | evidence |
|:--|:--|:--|
| C0 | DONE 2026-07-23: 4 arms registered (`509ba86`), PPO-Enc dim-sync fixed shared (`_core/runners/__init__.py`), smoke x2 per arm passed (artifacts preserved in `/workspace/.trash/smoke-ablation-reg-260723/`). **C0.5 DONE 2026-07-23 (audit session): all 4 arms correctly wired at code level** — NoEncoder actor gets policy obs only (`actor_critic_asym_constrained.py:113`), PPO actor obs_groups `["policy"]` + `OnPolicyDoraemonRunner`, NoIPO via `terms=[]` auto-sync, PPO-Enc matches the PolicyBase split protocol; stale 69D/97D docstrings in `rsl_rl_ppo_cfg.py` corrected to 72D/100D (`observation_space: 72` since biasema). **C0.4 DONE 2026-07-23 4/4**: every arm loads its smoke checkpoint through `eval.py static` (rc 0 + `summary.json`). PPO-Enc failed first (`ValueError: Policy obs dim 72 != expected 69`) — the EVAL path had no obs-width sync at all: `eval.py` maps only `ALBCConstraintEncoderRunner` to the syncing runner and every other arm falls through to stock `OnPolicyRunner`, which is fine for non-encoder actors but not for PPO-Enc (encoder policy + stock runner). Fixed by calling `sync_policy_obs_dim` at both runner-construction sites; re-verified 4/4. C0 has no residual left | git log; CHANGELOG 2026-07-23; task-reference.md; audit session 2; `/workspace/.trash/smoke-ablation-reg-260723/c04-eval/<arm>/summary.json` |
| C3 | NOT RUN — the largest remaining block: 4 arms x 3 seeds (30/31/32, paired with the anchor), workstation GPU0 serial, ~60 h. Proposed arm = the three B1a anchor runs themselves while final config == anchor config. LAUNCH NOTE (from C0.5): `Isaac-ConstrainedALBC-TRPO-NoIPO-v0` inherits `wandb_project="att_dr_harder"` + `logger="wandb"` from the production cfg, so that arm silently logs to the wrong project unless `--log_project_name`/`--run_group` are passed explicitly — pin both on every C3 launch | roster section; budget section 8 |
| C4 | PARTIAL: s30 student distilled (`trpo_buoyfix_s30_tcn_260722_184307/184632`) under the cuDNN-disabled slow path; full C4 = per-FINAL-teacher distillation + `export_deploy.py --golden` pack + C4a latent-collapse diagnostic | student tree; wiki cudnn page |

## 5. Re-judgment of every remaining item (KEEP / DROP / MODIFY / ADD)

| item | verdict | deciding evidence |
|:--|:--|:--|
| B0b/B1b curriculum recalibration TRIPLE | **MODIFY -> deferred with reactivation edge**. Budget-conditional: at the adopted 5000-iter budget the curriculum is iteration-limited, not bounds-limited (anchor Beta a 12.900 -> 1.670, 0/20 box-bound at 4750) so widening is inert; at 8k+ the box saturates (iter ~7000) and widening becomes the only lever. No 8k+ run remains on the roster (extensions rejected twice, Arm I cancelled) -> B0b fires ONLY if an 8k+ regime is ever re-rostered, and must then precede it | `diagnose-20260723-134359` (Beta table), `diagnose-20260720-124259` (saturation), wiki Z2 |
| B0c/B1c max_thrust DR band | **KEEP, re-parented onto B1a config** (B1b no longer exists ahead of it). One variable, band SOURCED (±15%). Paired-seed: 3 runs vs the 3 anchor seeds, ~15 h. Runs BEFORE C3 because adoption changes the final config. Residual: battery-voltage window memo (Z6). TAM-arm band stays excluded (no source) | wiki `sim_hydro_nominal...`; seed-floor methodology |
| B1d latency arm | **DROP as scheduled item; deferred with edge** — Z4 instrument does not exist and delay is off-DORAEMON (stalls the curriculum, e1 lesson). Edge: build Z4, then re-propose. User direction (latency wanted in final training config, 2026-07-20) recorded, not actionable yet | wiki latency page (both blockers re-verified) |
| B2 scale-up | **DROP**. Arm N (envs x2 at 5k) NULL; iteration extension answered net-negative twice (extend8k, moreiters); Arm I cancelled as a third dose of the same lever. The campaign's literal question ("scale after the box is widened") is moot while B0b is deferred — reactivation edge shared with B0b | wiki e3 page (closed 2026-07-23); reports |
| B3 joint1 Stage-2 | **DEFER** (unchanged): requires a station-keeping-on-unlimited-physics checkpoint that does not exist; not on the final-model path | wiki joint1 page |
| B1a-dgx replication | **KEEP as OPTIONAL, human-gated** — already queued; stakes low (discriminates a 9.6%-of-sigma effect); C3 does not wait for it [AUDIT 2026-07-23: recommend **DROP** — same-config same-seed cross-machine delta is +109% on roll ss_error (section 11.2), so a DGX anchor cannot discriminate anything about the workstation anchor; decision stays with the human] **-> user DROPPED 2026-07-23** | proposal `next-20260723-dgxanchor`; section 11.2 |
| A6 (sigma-R6) + Z8 (sigma-R1) | **DEFER both** — R1 is not in code (grep-verified; the "Z8 shipped" record was wrong) and nothing on the roster consumes it now that R6 is deferred; zero adopted levers + 56% seed floor make another ±5% tuning probe paired-seed-expensive with no motivating deficiency. Edge: a future reward-kernel experiment (R1 must land first, behavior-preserving) | grep; wiki reward_sigma page |
| Z10 penalty rescale | **DROP — close resolved-by-gate**: the page's own gate (measured deficiency) answers itself; penalties are 1.4% of reward | report; wiki page |
| Z3 encoder sweep | **KEEP (W0)** — zero-GPU rule-03 hygiene on the anchor checkpoint | rule 03 |
| C0 residuals (C0.4, C0.5) | **KEEP (W0)** — cheap; a mislabelled arm invalidates the comparison it anchors | roster C0 items 4-5 |
| C3 comparison set | **KEEP** — machine decided: **workstation** (e3 NULL means the final model is the workstation Stage-B model; the plant fix lives only on the workstation editable install). 12 runs paired-seed [AUDIT-CORRECTION 2026-07-23: "fix lives only on workstation" is wrong as stated — Arm N trained WITH the fix on DGX (its `env.yaml` `volume: 0.0079`); the binding reason is machine-comparability: cross-machine same-config same-seed delta +109% on roll ss_error, section 11.2. Workstation decision unchanged, on corrected grounds] | roster section 3 ordering argument; section 11.2 |
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

**LIVE-BACKLOG CORRECTION 2026-07-23 (post-consolidation drift, B0c session)**: the backlog is
live and has already moved. `omx wiki list --status needs-experiment` now returns **8**, not 7 —
`roll_transient_is_worst_at_none_dr_and_improves_monotonically_as.md` (created 2026-07-21,
unblocked) was never carried into section 6 or 11.7. Its disposition is now recorded in 11.7.
The count above is kept as the as-of-consolidation figure; treat `omx wiki list` as the
authority and re-enumerate at every session start rather than trusting this number.

## 7. Remaining-work sequence (dependencies explicit)

```
W0 (zero-GPU):            COMPLETE 2026-07-23 — C0.4 4/4 (eval-path obs-width sync
                          fixed en route), C0.5, Z3, Z6 all closed; see sections 4/11.7.
                          B0c is now the head of the queue.
Human decisions:          (a) B1a-dgx: DROPPED (user 2026-07-23, audit section 11)
                          (b) cuDNN cu12 image fix (recommended before C4)
                          (c) DGX plant-fix hand-replication (only needed if DGX rejoins)
                          (d) repeatability run: DECLINED (user 2026-07-23) — screening
                              floors stay on the conservative indirect estimate (11.6)
B0c  (after W0):          max_thrust ±15% DR arm vs anchor -> D3. SINGLE-SEED SCREENING ONLY
                          (user 2026-07-24, reaffirmed seed aversion): seed 30, paired vs
                          trpo_buoyanchor_s30, ~5 h (11.6 item 3). The old "stage 2 = seeds
                          31/32" multi-seed confirmation is CANCELLED -- not run in this
                          campaign. Any multi-seed run is deferred to an explicit paper-phase
                          request (user doubts it is needed at all). Per 11.6 item 5 (SPLIT,
                          not repealed) a single-seed number is a config screening verdict,
                          never a paper claim: a stage-1 clear makes B0c a candidate config to
                          carry forward, NOT a seed-confirmed adoption.
                          Proposal: next-20260723-203114 (label B0c) -- APPROVED by independent
                          review after TWO `revise` rounds; supersedes next-20260723-175314 and
                          next-20260723-202249, both retained unchanged for audit. QUEUED
                          2026-07-23 (`.omx/runs/trpo_b0cmaxthrust_s30_PLACEHOLDER/`,
                          queued_commit 766219e, 4 gates acked). LAUNCHED 2026-07-24 02:43
                          (human-approved) -> run trpo_b0cmaxthrust_s30_260724_024326, seed 30,
                          workstation GPU0; eval+verdict run autonomously on completion (eval
                          is not gated), then STOP -- no further training without the human.
                          VERDICT 2026-07-24 07:38 (single-seed, TERMINAL): NULL -- neither
                          pre-registered floor crossed at none/roll (Δos_env_mean +2.03 pp vs
                          >=10 pp needed; Δss_error -0.027 deg vs >=0.10 deg). Eval
                          static_260724_073758 vs anchor static_260723_091813: roll os_env_mean
                          slightly HIGHER at none/soft/hard (+1-2 pp ~= +0.6 deg overshoot,
                          above the E1 ~0.33 pp eval-noise floor), ss_error unchanged within
                          noise (~0.04 deg), pitch flat, n_gt20 mixed/small. B0c does NOT clear
                          a screening floor improving-side (consistent with Stage A 5/5
                          zero-adoption). REFRAME: B0c is not a tuning knob but the SOURCED
                          max_thrust ±15% DR band (a needs-apply-before-retrain sim-fidelity
                          correction). NULL-on-nominal = applying the physically-correct band
                          costs ~nothing nominal (small transient +0.6 deg, DC offset flat)
                          while adding a robustness dim the anchor lacks. ADOPT-vs-KEEP is a
                          HUMAN call (SSOT 0b): keep anchor as final (tuning-null reading) OR
                          adopt B0c as the fidelity-correct baseline (apply reading) -> if
                          adopted, final teacher changes -> re-distill + re-run C4a(E4). Seeds
                          31/32 CANCELLED -- no confirmation run. Left for the human.
                          NOTE: B0c is a
                          CODE change (marinelab per-env max_thrust tensor + albc cfg/events +
                          dr_config none-collapse registration), not a config flip -- rule-02
                          baseline-tag/exp-branch isolation applies in BOTH overlay repos.
C3   DEFERRED (section 0b, user 2026-07-23): the 4-arm x 3-seed ablation set is a PAPER
                          artifact, not a config-selection instrument. Moves off the critical
                          path to a later paper phase, cost unchanged (~60 h) when it runs.
C4   (after B0c, no      distill final teacher -> golden pack -> C4a latent diagnostic
      longer after C3):   -> Stonefish diagnostic run (Z5 framing). C4 needs a FINAL TEACHER
                          CHECKPOINT, which the anchor already is unless B0c adopts -- it
                          never depended on the ablation set, so deferring C3 does not
                          block it.
```

Standing gates (unchanged): every training launch via `omx queue-launch` + human approval;
`marinelab` must stay on `exp/buoyancy-recenter` (checking out `main` silently reverts the
plant); deployment checkpoint rule pre-declared = median seed by none-level roll `ss_error`
(claim = the full paired distribution regardless of which seed ships).

## 8. GPU budget (measured, not estimated)

| resource | throughput | note |
|:--|:--|:--|
| Workstation RTX 4070 (GPU0) | 3.58 s/iter @4096 envs -> ~5.0 h per 5000-iter run | 11.3/12.3 GB at 4096 envs: comparison set is SERIAL on GPU0; the 8 GB 4060 evals |
| DGX GB10 | 5.409 s/iter @4096; 9.65 s/iter @8192 (13.41 h/run) | source build, `./isaaclab.sh -p` only; one job at a time. Plant fix IS present after all (stand-down 2026-07-23: `marinelab` on `exp/buoyancy-recenter` @ `db28b5a`, volume 0.00790 — content-equal to workstation `7d45c2c`), and cuDNN works there (torch 2.9.0+cu130, cudnn 91300, conv1d fwd/bwd with grad) where the workstation image is broken |

| block | runs | wall clock | on critical path? |
|:--|--:|--:|:--|
| B0c stage 1 (seed 30 only) | 1 | ~5 h | **YES — head of queue** |
| B0c stage 2 (seeds 31/32) | 2 | ~10 h | only if stage 1 clears, human-gated |
| C4 distillation | per teacher | ~5 h/pack until the cuDNN image fix; minutes after | YES |
| C3 ablation set (4 arms x 3 seeds) | 12 | ~60 h (~2.5 days serial) | **NO — deferred to the paper phase (0b)** |
| + proposed-arm re-run iff B0c adopts | 3 | ~15 h | with C3 |
| B1a-dgx (optional, human-gated) | 3 | ~~22.5 h (DGX)~~ DROPPED (user 2026-07-23) | no |

Critical path after the 0b pivot ≈ **10 h** workstation-serial (B0c stage 1 + one C4 pack),
plus analysis gates — down from 75 h, because the 60 h ablation set moved to the paper phase
rather than being cancelled. Total program cost is unchanged at ~70-95 h; what changed is
when it is spent and what it buys first.

### Machine allocation (what DGX gets, decided 2026-07-23)

Machine isolation (11.6 item 1) says campaign training runs on the workstation; it does
not say DGX is unusable. The split is by *whether the output is compared across machines*,
and every roster states DGX's slot explicitly — including when that slot is "idle this
block", so an idle GB10 is a decision rather than an oversight.

| work | machine | why |
|:--|:--|:--|
| Any run whose numbers enter a campaign comparison (B0c, C3, all anchors) | **workstation only** | identical config + identical seed differ by +109% on roll `ss_error` across machines (11.2); one DGX arm silently invalidates the set |
| C4 student distillation | **DGX candidate — human decision** | supervised imitation from a FROZEN workstation teacher checkpoint: the teacher is the file, not the machine, so no cross-machine term enters the comparison. DGX cuDNN works (stand-down 2026-07-23); the workstation runs the cuDNN-disabled workaround at ~70x slowdown. Deciding this is cheaper than the image fix, and does not block it |
| Instrument/tooling probes, smoke checks, load-checks | either | nothing is compared |
| A future DGX-trained campaign arm | **DGX, but only with its own anchor set** | rejoin condition: explicit roster allocation + plant fix present on DGX (satisfied, `db28b5a`) + a DGX-trained anchor to compare against. Never fold a DGX number into a workstation-anchored comparison |

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

## 11. Experiment-validity audit (2026-07-23)

Audited per `.sp/plans/2026-07-23-experiment-validity-audit-prompt.md`: for each of the
12 executed runs, could the design produce the verdict it reported? Every number below
was read from disk or computed from `summary.json` / `train/params/*.yaml` on
2026-07-23. Reports were read via `omx report-parse` only. Confidence tags:
HIGH = read/computed from a file; MED = inference across sources; LOW = judgment.
Reports are append-only (report-guard), so corrections to report text are recorded here
and in the wiki, never by editing a `report.md`.

### 11.1 Unit corrections (the root defect; it propagated into three documents)

- `ss_error` / `ss_jitter` are **degrees** (`constrained_albc/analysis/_analyze/recompute_metrics.py:167`:
  |actual_deg - target_deg|). HIGH.
- `os_env_mean` / `os_env_median` / `us_env_mean` are **percent of the step magnitude**
  (`recompute_metrics.py:109`: `(peak - target) / step_mag * 100`), NOT degrees. HIGH.
- `n_gt20` counts envs whose overshoot exceeds **20 percent of the step**, not 20 deg
  (`recompute_metrics.py:121`). HIGH.
- The static-eval schedule steps roll by exactly **30 deg** in every attitude segment
  (pitch 30 or 60 deg) — computed from `data_none.npz` target arrays. Roll
  `os_env_mean` in degrees = pp x 0.30, exact. HIGH.
- Consequences: anchor roll os 15.86 pp = **4.76 deg** peak beyond target (95% of the
  4.985-deg settling gate — not "318%"); plant-fix os shift -3.93 pp = **-1.18 deg**
  (24% of the gate — not "-3.93 deg" / 79%). The "(deg)" mislabel originated in report
  `diagnose-20260723-134359` (its tables print "os_env_mean (deg)") and propagated into
  section 0 of this document and into the audit prompt itself. HIGH.
- The audit prompt's own "A5 +16.8% = +0.065 deg" is also wrong: it applied the
  percentage to the corrected-plant anchor mean (0.390) instead of A5's actual baseline
  (biasema 0.2149). Actual: **+0.036 deg = 3.1% of one sigma**. HIGH.

### 11.2 Reference scales and measured floors (roll, `none` level)

| quantity | value | source | conf |
|:--|--:|:--|:--|
| obs-noise sigma, euler | 1.146 deg (0.02 rad) | `envs/main/config.py:271-274` | HIGH |
| `rp_vel_settling` gate | 4.985 deg (0.087 rad) | `envs/main/mdp/constraints.py:222` | HIGH |
| eval determinism | exact repeat | biasema evaluated twice independently (2026-07-15 19:35 and 07-16 16:11, different files/md5), metrics identical to 4 sig figs; all run-to-run variance is training-side | HIGH |
| eval-code drift 07-15..07-22 | none | `git log --since=2026-07-15 --until=2026-07-22 -- constrained_albc/analysis/` is empty; biasema and Stage-A evals ran the same code | HIGH |
| cross-seed floor, old plant (UNPAIRED) | 74.8% p2p = 0.241 deg ss_error | `seed_floor_dgx` 3 seeds | HIGH |
| cross-seed floor, corrected plant (UNPAIRED) | 56.0% p2p = 0.218 deg | buoyanchor 3 seeds | HIGH |
| paired same-machine scatter bound (one-lever 5k arms vs biasema: A2/A3/A5) | -5.8% .. +16.8% (max 0.036 deg) | `summary.json` deltas; n=3 and the levers may carry true effects, so this is an upper-bound-flavored bound | MED |
| cross-machine, same config + same seed (n=1 pair) | **+109% ss_error (+0.235 deg), +6.4 pp os, +31.3 envs n_gt20** | dgxseed30 (DGX, `usd_path /home/seungmin/...`) vs biasema (workstation); config diff = usd_path prefix + wandb project ONLY, seed 30 both | HIGH |

Reading: the +/-5% adoption band (+/-0.011 deg on the biasema base) is ~1% of one
obs-noise sigma and far below every floor above — undecidable under any design. The
correct decidability scale is run-to-run training variance (eval is deterministic);
sigma is the physical-relevance scale. Same-machine paired deltas under ~0.04 deg are
indistinguishable from lever-free scatter. Cross-machine comparisons are meaningless
below ~0.24 deg.

### 11.3 Part A — 12 executed runs, 7 checks each

Checks: (1) metric resolution, (2) baseline identity, (3) plant identity, (4) DR-level
fairness (`none` only), (5) manipulation applied, (6) metric-hypothesis match,
(7) answer was NOT available without training. ok = passes; W = caveat in notes.

| run | 1 | 2 | 3 | 4 | 5 | 6 | 7 | verdict | follow-up |
|:--|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:--|:--|
| A1 `stepint400` | ok | ok | old | ok | ok | ok | ok | **VALID** — H1 refutation robust | none |
| A2 `entcoefzero` | ok | ok | old | ok | ok | ok | ok | **VALID** (diagnostic) | none |
| A3 `minstdthr008` | W | ok | old | W | ok | ok | ok | **VALID as screening DISCARD**; effect-size claim INCONCLUSIVE | (c) moot |
| A4 `privslim24d` | W | ok | old | ok | ok | ok | ok | **VALID** — FAIL decidable | none |
| A5 `budgetslack` | W | ok | old | ok | ok | ok | W | **VALID as NULL** (tracking); transient trade real-looking (11.5) | (b) re-analyzed here |
| `dgxseed30` | ok | n/a | old | ok | ok | ok | ok | **VALID** (measurement) | none |
| `dgxseed31` | ok | n/a | old | ok | ok | ok | ok | **VALID** (measurement) | none |
| `dgxseed32` | ok | n/a | old | ok | ok | ok | ok | **VALID** (measurement) | none |
| `buoyanchor_s30` | ok | W | new | ok | ok | ok | ok | **VALID** (anchor); C-B retrain claim **INVALID-BY-BASELINE** | (c) moot, plant never reverts |
| `buoyanchor_s31` | ok | W | new | ok | ok | ok | ok | **VALID** (anchor) | none |
| `buoyanchor_s32` | ok | W | new | ok | ok | ok | ok | **VALID** (anchor) | none |
| Arm N `e3scaleN_envs8192` | ok | **X** | new | ok | ok | ok | W | **INCONCLUSIVE** as "envs have no effect" (cross-machine baseline); the no-adoption DECISION stands | (c) closed lead stands, scoped |

Count: 12 runs x 7 checks = 84 checks reported. Notes:

- **A1** (8000 iters, `model_7999`): baseline = `extend8k` at 8000 iters — intended and
  fair (isolates `step_interval` 250->400 at fixed budget; `env.yaml:513` shows 400 vs
  biasema 250, HIGH); ref5k biasema shown for context. Bands were pole predictions, not
  +/-5%: H1 pole 17.0 pp os (5.10 deg), H2 pole 25-27 pp (7.5-8.1 deg), measured 30.55 pp
  (9.16 deg). Distance from H1 = 13.5 pp = 4.06 deg >> all floors -> **H1 refuted,
  decidable** (HIGH). Distance from H2 = 3.6 pp = 1.07 deg, within plausible paired
  transient scatter -> the secondary "H2 also missed" is INCONCLUSIVE (MED); the
  headline verdict does not depend on it.
- **A2**: manipulation = `entropy_coef_per_dim (0.0 x8)` vs biasema `(0.01 x2, 0.001 x6)`;
  per-dim overrides the scalar (`_core/algorithms/constraint_trpo.py:68,107`), so the
  yaml's scalar `entropy_coef: 0.003` is dead — manipulation APPLIED (HIGH). Verdict
  reads TB sigma trajectories (deterministic logs), not an eval band — resolution
  concerns do not apply to the mechanism claim.
- **A3**: manipulation = `min_std_per_dim` thruster dims 0.05->0.08 (arm dims 0.1
  unchanged) — APPLIED (HIGH). Its primary band required a -10% os improvement
  (-1.7 pp = -0.51 deg), below the paired transient scatter (unrelated levers moved os
  by +7.7 / +9.3 pp) -> the adoption bar was **undetectable by design**
  (band-invalid-by-resolution); measured +4.5 pp (+1.34 deg) is also within that
  scatter -> "actively worsens" unproven (MED). The DISCARD stands on burden: the
  pre-registered improvement was not demonstrated. Alt clause read at `hard` violates
  DR fairness (check 4 W) but decided nothing (it also failed).
- **A4**: manipulation = `state_space: 24` vs 28 (`env.yaml:96`) — APPLIED (HIGH). Band
  +/-5% (+/-0.011 deg) is band-invalid-by-resolution, but the measured effect is
  +0.158 deg roll / +0.185 deg pitch (14-16% of sigma), 3.5-4x the paired scatter
  bound, coherent across both axes AND CV -> **FAIL decidable despite the band** (MED-HIGH).
- **A5**: manipulation = budgets `rp_vel_settling` 0.2->20.0 and `manipulability`
  0.05->5.0 (x100, `env.yaml` diff vs biasema) — APPLIED (HIGH). Tracking delta
  +0.036 deg = 3.1% sigma, inside paired scatter -> NULL correct. Check 7 W: the
  constraint-inertness half (J_C/d_k margins) was already visible in anchor TB without
  a run. See 11.5 for the transient-trade upgrade.
- **dgxseed30/31/32**: purpose = UNPAIRED cross-seed floor; valid as such. The wiki
  page itself already forbids cross-GPU comparison. Their `static_260723_*` re-evals
  (B0a-eval, `PLANT.txt` markers) provide the clean B-A plant shift (same policy,
  eval-only plant swap) — VALID (HIGH).
- **buoyanchor s30/31/32** check 2 W: the A->B->C decomposition's C-B ("retrain")
  compares DGX-trained policies (B) against workstation-trained policies (C), so
  "+0.110 deg retrain cost" bundles the machine term (+0.235 deg on the only measured
  same-config pair) with the retrain term — **INVALID-BY-BASELINE as a retrain
  measurement** (HIGH on the confound's existence; the sign/size of the pure retrain
  term is unknown). B-A (plant, eval-only) is clean. "Anchor SOUND" survives: no
  adverse absolute signal, in-family with the posttam distribution, physically
  motivated fix.
- **Arm N** check 2 X: trained on DGX (`usd_path /home/seungmin/...`, HIGH) with the
  corrected plant (`volume: 0.0079`, HIGH), judged against WORKSTATION anchors — a
  cross-machine comparison with a measured +109% machine term. "Inside the anchor
  band" therefore cannot attribute the null to envs. The DECISION (do not adopt
  8192@DGX) stands independently: no benefit demonstrated + machine-comparability
  forbids DGX-trained finals anyway.
- **Arm I** (12k iters on DGX, stopped before artifacts): stopping was RIGHT —
  a third dose of a twice-net-negative lever (extend8k, moreiters), on a
  cross-machine-confounded rig, in a regime (8k+) that is off-roster while B0b is
  deferred. HIGH.

### 11.4 The three suspected defects, adjudicated

- **D1 (verdict metric below physical resolution): CONFIRMED in conclusion, corrected
  in mechanism and units.** The +/-5% band is dead (11.2), but because of run-to-run
  training variance, not obs-noise per se — eval is deterministic, so sigma (1.146 deg)
  is the physical-relevance scale, not a measurement floor. The os rows of the prompt's
  table were unit-mislabeled (11.1); the overshoot axis is genuinely the largest
  absolute deficiency (anchor 4.76 deg peak-beyond-target vs 0.39 deg ss_error), so the
  prompt's direction survives the correction.
- **D2 (Stage A on a later-corrected plant): timeline CONFIRMED** (marinelab `7d45c2c`
  2026-07-22 13:36; all Stage-A runs started 2026-07-20 18:02 .. 07-21 18:11 and carry
  `volume: 0.009`, HIGH). Consequences re-scoped: the plant term on the verdict axis
  (ss_error) is only -0.043 deg paired — the plant win is on the transient
  (-1.18 deg os, n_gt20 -19.3/-12.7/-0.3 per seed = a removed failure mode in 2 of 3
  seeds). Transport: A1/A2 are mechanism verdicts (training dynamics) — transport
  (MED); A3/A5 are burden-based no-adoptions — nothing to transport; A4 is an
  information-ablation with an effect ~4x the paired floor — plausibly
  plant-independent (MED). **No Stage-A re-runs are warranted.**
- **D3 (seed-floor misapplied to paired comparisons): premise CONFIRMED** — all 10
  posttam runs carry `seed: 30` (every `agent.yaml` read, HIGH). Wiki `cc06451` is
  **right-but-mis-scoped**: right that +/-5% is dead and that paired designs cancel the
  seed term, wrong to label the already-paired Stage-A verdicts undecidable by the
  UNPAIRED floor — under the paired analysis A4 is decidable-FAIL and A5 is NULL, which
  the page's own examples get backwards. The genuine limits are: (a) same-seed pairing
  survives only WITHIN one machine (+109% cross-machine pair); (b) the same-machine
  paired repeatability floor is unmeasured (bounded above by the 11.2 scatter bound).
  Correct protocol in 11.6.

### 11.5 Re-analysis on transient metrics (existing eval data, zero GPU)

All 12 runs + baselines re-read on `os_env_mean` / `n_gt20` / `rise_time`
(`summary.json`, `none`, roll). What changes:

| run | os pp (deg) | n_gt20 /64 | rise s | new reading |
|:--|--:|--:|--:|:--|
| biasema (ref5k) | 17.02 (5.11) | 4.3 | 0.403 | uniquely clean tail — every other old-plant run shows 21-61 envs |
| extend8k | 26.99 (8.10) | 61.3 | 0.361 | the 8k extension's real cost: 96% of envs overshoot >6 deg — reinforces B0b deferral and the Arm-I stop |
| A1 | 30.55 (9.16) | 53.7 | 0.333 | + ss_error +52.9% (+0.090 deg) vs extend8k: additional evidence against si400 beyond the os verdict |
| A2 | 24.70 (7.41) | 42.7 | 0.332 | entropy removal degrades the tail while return rises — confirms "reward up" is an unsafe adoption criterion |
| A5 | 26.35 (7.90) | 54.7 | 0.307 | rise -24%, os +9.3 pp (+2.8 deg), n_gt20 +50: a coherent released-damping signature of `rp_vel_settling` x100 -> the constraint is inert in J_C margins but NOT inert in transient shaping (MED-HIGH); "learner near-twin of anchor" needs this scope |
| anchor 3-seed | 15.86 (4.76) | 12.1 | 0.539 | plant fix trades slower rise (+0.14 s) for a smaller tail |
| Arm N | 16.08 (4.82) | 13.3 | 0.528 | inside anchor band, unattributable (cross-machine) |

### 11.6 Corrected decision protocol (supersedes the +/-5% band everywhere)

1. **Machine isolation**: never compare runs trained on different machines; a machine
   that hosts training needs its own anchor. (Evidence: 11.2 cross-machine pair.)
2. **Units**: pre-register every band in absolute units — deg for ss_error, pp AND deg
   (x0.30 roll) for overshoot. Percent-only bands are how this campaign broke.
3. **Screening** (per probe arm): 1 paired run, same seed, same machine as its
   baseline. Call an effect REAL only if |d ss_error| >= 0.10 deg (~2.5x the scatter
   bound) or |d os| >= 10 pp (3.0 deg) or |d n_gt20| >= 15 envs; roll+pitch sign
   coherence strengthens. Below the floors: NULL/INCONCLUSIVE, never "worse"/"better".
4. **Adoption confirmation**: 3 paired seeds vs the 3 anchor seeds; adopt only if 3/3
   sign-consistent AND the mean paired delta clears half the screening floor.
5. **Paper number**: the full 3-seed distribution; pre-declared median-seed deployment
   rule (unchanged, section 7). **SPLIT 2026-07-23 (section 0b), NOT repealed**: tuning
   and screening now run single-seed paired, which is sound for screening because pairing
   cancels the seed term — but a single-seed result is NEVER a paper number. The ablation
   table still requires the deferred 3-seed C3 set. Do not let a screening number migrate
   into the paper by inheritance; if a table cites fewer than 3 seeds, it is a screening
   table and must say so.
6. **UNSETTLED — the true same-machine paired repeatability floor.** Everything in (3)
   uses an n=3 upper-bound-flavored scatter estimate. One repeat run (identical config
   AND seed to `trpo_buoyanchor_s30`, workstation, ~5 h) would measure it directly.
   DECLINED by user 2026-07-23 — remains unsettled by choice; use the conservative
   floors in (3) and do not re-propose without new motivation.

### 11.7 Part B — every not-yet-run item (11 open wiki leads + roster items)

| item (wiki slug / roster id) | verdict | deciding evidence |
|:--|:--|:--|
| `closed_loop_latent_collapse...` -> C4a | **KEEP** | eval-only, cheap, unblocked; unaffected by this audit |
| `curriculum_recalibration...` -> B0b | **KEEP-DEFERRED** (8k+ edge, unchanged) | audit strengthens: the 8k regime's transient cost restated in degrees (extend8k os 8.10 deg, 61/64 envs >20% — 11.5) |
| `experiment_idea_latency...` -> B1d/Z4 | **DEFER** (unchanged) | Z4 instrument absent (grep at HEAD, section 4 Z4); both blockers stand |
| `joint1_stage_1_gate...` -> B3 | **DEFER** (unchanged) | prerequisite checkpoint does not exist |
| `reward_sigma_integral_obs_gate...` -> A6/R1 | **DEFER** (unchanged) | R1 absent at HEAD (grep, section 4 Z8); no consumer |
| `stonefish_yaw_gap...` -> Z5 | **KEEP** as deployment diagnostic (unchanged) | separate machine; framing already correct |
| `thruster_nonlinear_curve_t200...` | **DEFER** (unchanged) | bench hardware |
| `container_cudnn_is_cu13...` | **KEEP** as C4 infra, human-gated (unchanged) | throughput-only blocker |
| `imu_45deg_offset...` | **DEFER** (unchanged) | user decision 2026-07-20; robot bring-up track |
| `sim_hydro_nominal...` (max_thrust) -> B0c | **KEEP, MODIFY the decision rule** | run as planned (3 paired seeds vs anchor seeds, ~15 h, before C3) but judged by protocol 11.6 items 2-4, NOT +/-5%; pre-register the band in deg at proposal time |
| `tam_vertical_single_motor...` | **DEFER** (unchanged) | m4 HW fault |
| W0 (C0.4, C0.5, Z3) | **KEEP** | zero-GPU hygiene, unchanged. Z6 battery memo verified DONE 2026-07-23 (4S LiPo 14-16.8 V recorded on the `sim_hydro` wiki page; +/-15% band kept, conservative) — removed from the remaining W0 set |
| B1a-dgx (queued) | **MODIFY -> recommend DROP** | a DGX anchor cannot discriminate the workstation anchor across a +109% machine term (11.2); would spend 22.5 h to measure a machine effect already measured on the old plant; human-gated |
| C3 comparison set | **KEEP but DEFERRED to the paper phase** (user 2026-07-23, section 0b) — still 12 runs / 3 seeds per arm / workstation serial / ~60 h when it runs; off the critical path until then. Single-seed screening does NOT substitute for it | 3 seeds/arm is the paper protocol (11.6 item 5, now SPLIT not repealed — see 0b); machine rationale corrected in section 5 |
| C4 deployment pack (+C4a) | **KEEP** | unchanged; cuDNN fix recommended first |
| ADD: repeatability run (exact config+seed repeat of `trpo_buoyanchor_s30`) | **DECLINED by user 2026-07-23** (no appetite for extra measurement runs) | do not re-propose without new motivation; screening verdicts use the conservative indirect floors of 11.6 item 3, stated with their n=3 caveat |
| ADD (drift, 2026-07-23): `roll_transient_is_worst_at_none_dr_...` | **CARRY as a zero-GPU eval-side probe, DEFERRED behind C3** — not on the final-model critical path and NOT addressed by B0c (B0c perturbs thruster authority; this lead is about the inverted DR-level scaling of the roll transient). Its own candidate mechanism (a), "eval-protocol artifact — `eval.py static` grades each run on its own learned DR box", is testable with NO training via the shared-exam path (`--doraemon-dr-from`), the same instrument already used by `next-20260716-144615`. Re-propose after C3, when the 12-run set makes the inversion checkable across arms instead of the 2 runs it currently rests on | wiki page (2 runs, HIGH); precedent proposal `next-20260716-144615` |

Forward plan and GPU budget (sections 7-8) are otherwise unchanged: critical path
~75 h workstation-serial; B1a-dgx recommended drop removes 22.5 h from the optional
pool; the proposed repeatability run adds 5 h if approved.

### 11.8 What this audit could not settle

- The same-machine paired repeatability floor (11.6 item 6) — needs the proposed
  repeat run.
- Whether 8192 envs has any effect at all: Arm N is cross-machine-confounded; a clean
  answer needs a workstation 8192 run (~10+ h) that nothing currently motivates — not
  proposed.
- Whether biasema's uniquely clean tail (n_gt20 4.3 vs 21-61 everywhere else on the old
  plant) is the bias-ema effect or a fortunate draw — single-seed, old plant, moot for
  the forward path (the anchor family retains the biasema config).
- The pure retrain term of B1a's C-B leg (machine-confounded); moot — the plant never
  reverts, so no decision consumes it.

## 12. Post-fault-DR roster (2026-07-27) — open human gates and remaining experiments

Context: the FaultDR-AB campaign (group `fault_dr`, proposals `next-20260725-155325`
FTC-m4 and `next-20260725-175508` FaultDR-AB) concluded 2026-07-27. Verdict (report
`fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324`;
wiki `ftc_fault_dr_a_b_result_2026_07_27_...`): fault-DR **recommend-ADOPT** (5-12x less
m4-dead attitude degradation at none/medium/hard, zero fault terminations, mechanism =
heavy-tail removal; `soft` excepted at 1.2-2.5x), privileged fault obs **NOT adopted**
(H2, resting on the absence of a floor-clearing Arm-B advantage; n=1 seed per arm).
Most consequential open finding: the `fault_severity` curriculum ended at 7.7% (Arm A) /
9.6% (Arm B) of its [0,1] range and was still rising at iter 4750 — under 6% of envs
ever carried a degraded thruster, so fault-DR's ceiling on this plant is UNMEASURED.
Human-facing consolidated PDF: `/workspace/.sp/reports/fault-dr-ab-260727/`.

### 12.1 Open human gates (decisions, zero GPU)

| gate | decision | interaction |
|:--|:--|:--|
| D-b | **DECIDED 2026-07-27: ADOPT (user)** — fault-DR (Arm A config family) enters the final teacher config; single-seed screening caveat (11.6 item 5) still applies to any paper claim. Final checkpoint pends E-ftc1 (its winner may supersede Arm A) and gate D-a (E-int if D-a also adopts) | final teacher changes -> re-distill C4 + re-run the C4a/E4 latent diagnostic |
| D-a | **DECIDED 2026-07-27: ADOPT (user)** — the sourced +/-15% max_thrust band enters the final config as a sim-fidelity correction (section 7 reframe); closes the `sim_hydro` max_thrust apply-gate | both gates now adopted -> E-int integration retrain becomes the final-teacher path |
| D-c | cuDNN cu12 image fix vs DGX-hosted distillation (unchanged from section 5) | throughput-only; blocks nothing else |

Queue hygiene: all four `.omx/runs/` pending artifacts are STALE, none is a live gate —
`trpo_b0cmaxthrust_s30_PLACEHOLDER` (launched 2026-07-24 as `..._260724_024326`),
`trpo_stepint400_260720_180208` and `trpo_baseline_260713_031325` (both launched on
their dates), `trpo_buoyanchordgx_s30_PLACEHOLDER` (user-DROPPED 2026-07-23).

### 12.2 Training candidates (all human-gated; priority order)

| id | one variable | machine / cost | readout |
|:--|:--|:--|:--|
| **E-ftc1** (DONE 2026-07-29) | **VERDICT 2026-07-29: H1-WEAK -- TREATMENT REJECTED.** Run `trpo_ftc1sevinit_s30_260729_105510`, report `analysis/diagnose-20260729-171553/report.md`. Achieved `fault_severity` 0.1929 vs the 0.20 H1 bar. Nominal cost at `none` is an axis trade (roll transient tail improves, pitch steady-state degrades, net attitude below floor) and the within-run m4-dead penalty is **2.9x-5.5x LARGER than Arm A at every DR level** -- the 2.50x severity head start made fault rejection WORSE, the opposite of the arm's purpose. Injection verified to bite (`fault_thruster_4` = 0.0 in 64/64 envs at all four levels), so this is a real result, not a no-op artifact. Disposition: `fault_severity` stays at the Arm A nominal 0.0; E-int remains the final teacher. Config change reverted on `exp/ftc1-severity-init` (`19c9b0e`, which also restored the adopted `max_thrust_scale` band the arm had deliberately switched off). Original scope: `fault_severity` exposure budget: faster severity schedule at the FIXED 5000-iter budget (NOT an 8k extension — twice-net-negative lever, sections 5/11.5); exact lever (initial Beta spread vs per-dim pacing) pinned at proposal time | workstation, ~5 h, seed 30 paired vs Arm A | achieved `fault_severity` mean (engine G3 table) + the same paired healthy/m4-dead eval via `compare.py paired`, floors 11.6 item 3. WATCH: `thruster_util` (Arm A already at 0.902 of budget) — if it binds at higher severity, budget redesign becomes its own follow-up arm rather than a confound inside this one |
| **P1-isaac** (zero training, GPU-using) | Isaac-side replay of the 5 shared joint1-swing profiles (S5 null / S2 30 deg min-jerk T=1 s / S1ff 90 deg min-jerk T=1 s / S3 sine 0.5236 rad 0.25 Hz / S4 same 0.75 Hz), joint2 pinned 0, zero action, DR+faults off; measures the base yaw reaction under the same protocol the Stonefish side completed 2026-07-29. Handoff prompt received from the Stonefish session 2026-07-29; script `scripts/isaac_p1_replay.py` already staged (sha256 `d9acb55b...5dda0` VERIFIED on disk; untracked, vault original `tools/p1_joint_swing/isaac_p1_replay.py`). **Source-verified 2026-07-29** -- all 12 env claims hold: `action_space` 8 (config.py:436); `_joint_pos_targets += delta` is ADDITIVE (albc_env.py:724) so a zero action is a true no-op and the script's direct write survives; `_apply_action` (albc_env.py:927) pushes the target and applies hydro every physics substep; `randomization.enable=False` genuinely zeroes the ocean current -- `_reset_physics` returns early at albc_env.py:1524 BEFORE `randomize_ocean_current`, `OceanCurrent._velocity_w` is zero-initialised and zeroed on reset, and `ou_enable` defaults False (config.py:562); asset `joint_pos={"joint.*": 0.0}` (marinelab albc.py:197) so pinning joint2 at 0 causes NO unintended initial swing despite `nominal_joint_pos=(0, pi/2)`; no clamp exists on `_joint_pos_targets`; 50 Hz = sim.dt 0.005 x decimation 4, matching the Stonefish command rate; episode budget 1500 steps vs the 1000 logged. **TWO ADDITIONS the handoff did not state**: (a) `velocity_limit_sim = 3.1 rad/s` (marinelab albc.py:206) is a SECOND saturation channel -- S1ff peak commanded velocity 2.945 rad/s = **95% of cap**, S4 80% -- so peak `\|dq1\|` vs 3.1 MUST be reported alongside peak `\|tau1\|` vs 13.0, or a velocity-clip divergence gets misread as torque saturation on exactly the two cases (S1ff, S4) the Stonefish side already found torque-saturated; (b) the only non-NaN termination is attitude > pi/2 (albc_env.py:1395; there is NO depth or position bound), so a `TRUNCATED` S1ff means the base tipped past 90 deg -- a physical result, not a script failure. Execution note: this session already runs INSIDE `marinelab-isaaclab` (compose `working_dir` + absent `/workspace/marinegym` confirm it is not the same-path legacy container), so the handoff's `ssh` + `docker exec` wrapper collapses to the inner command; and writing `--outdir` under `/workspace/...` (the `${WS_ROOT}` bind) removes the `docker cp` retrieval step entirely | workstation **GPU0**, sequenced AFTER `trpo_ftc1sevinit_s30_260729_105510` releases it (~16:31 KST) -- REVISED 2026-07-29 by user instruction: GPU1 is reserved for the concurrent student-track session (`exp/student-distill-eint`) and must not be used, and GPU0 cannot be shared now (E-ftc1 holds 11.4 of 12.3 GB, leaving too little for an Isaac Sim instance). ~5 min pure sim total, Isaac boot dominates; 5 cases x 3 reps. Smoke S5 x1 first. Proposal `next-20260729-124437` (lint ok, novelty clean), QUEUED | peak base `\|wz\|` and yaw excursion per case against the Stonefish CSVs; aggregate with `P1_STENCIL=3` (Isaac logs 50 Hz vs Stonefish 100 Hz -- the default 5-sample stencil spans 80 ms here vs 40 ms there and would smooth Isaac's peaks harder). **Unblocks the HydroRC recenter-v2 arm choice** -- all three candidate arms hinge on this number |
| **E-ftc1-confirm** (CLOSED WITHOUT A RUN 2026-07-29) | **VOID: the precondition failed.** E-ftc1 returned H1-WEAK, and the pre-registered rule discards this entry on anything but H1. No run directory exists under `fault_dr` (only Arm A, Arm B-priv and ftc1sevinit) -- with the parent treatment rejected, restoring the adopted band on top of a net-negative severity delta has nothing left to confirm. The `.omx/runs/trpo_ftc1confirm_s30_PLACEHOLDER` queue artifact is stale. Original design: `max_thrust_scale` `(1.0, 1.0)` -> the adopted `(0.85, 1.15)` band, `fault_severity` nominal held at 0.0771. **Launch precondition: E-ftc1 returns H1 (achieved severity >= 0.20). On H1-WEAK the pre-registered response is analysis-only with NO new run; on H2 there is no gain to confirm -- DISCARD the queue entry in both cases.** Rationale: E-ftc1 measures the ceiling on Arm A's plant, which has MORE actuation authority than the final teacher's, while `thruster_util` `J_C/d_k` already sits at 0.902 there (anchor 0.805 / band-only 0.853 / E-int 0.821). E-int's measured sub-additivity (0.821 where exact additivity would give 0.950) is evidence the two knobs contend for one budget -- the HAZARD, not reassurance; independent review caught that being cited backwards in the E-ftc1 proposal. Design bonus: this cell completes a seed-30 2x2 whose other three cells are already on disk (ArmA `(1.0,1.0)`/sev 0.0, E-int `(0.85,1.15)`/sev 0.0, E-ftc1 `(1.0,1.0)`/sev 0.0771), factor levels read from each run's as-run `env.yaml`. Caveat carried: the E-int cell is STITCHED (resumed from `model_2350.pt`, DORAEMON restored mid-curriculum at 0.0178, env RNG restarted), so the difference-in-differences is a SUPPORTING read and the verdict rests on the direct E-int comparison. Proposal `next-20260729-125443` (lint ok, novelty clean), QUEUED | workstation GPU0, ~5 h; GPU0 order E-ftc1 -> P1-isaac -> this (~17:00-22:00). GPU1 reserved for the student session | achieved `fault_severity` >= 2x E-int's iteration-matched 0.0770 (bite threshold 0.154) + the same paired healthy/m4-dead eval vs E-int's 17.78 / 8.43 / 20.38x, floors 11.6 item 3, exam restricted to `none` + within-run deltas. `thruster_util` reported regardless: binding = budget redesign is a SEPARATE arm, not "no benefit" |
| E-int | integration retrain (anchor + B0c band + fault-DR). **VERDICT 2026-07-28: H1 (sub-additive) -- this checkpoint IS the final teacher.** Original launch `trpo_eint_s30_260727_160913` (16:09, human-approved) CRASHED at iter ~2390/5000 on an Isaac Sim internal fault (`carb.tasking/Mutex.cpp:103` assertion `m_recursive`, C++ abort; learning was healthy -- reward 260.5, zero terminations, no NaN/OOM). RESUMED (human-approved) from `model_2350.pt` as **`trpo_eint_s30_rs2350_260727_195102`** with `--max_iterations 2650`, completed 4999/5000. Instruments vs anchor `trpo_buoyanchor_s30_260722_134743`: `thruster_util` J_C/d_k **0.821** (ladder anchor 0.805 / B0c 0.853 / ArmA 0.902; exact additivity would be 0.950 -> sub-additive, H2 refuted on its own mechanism); m4-dead att_norm advantage **17.78x / 8.43x / 20.38x** at none/medium/hard (worst gated 8.43x vs the 5x H1 bar; beats single-knob ArmA 6.33/7.24/8.04x at every level); `soft` 2.03x descriptive (no threshold, ArmA 1.17x); zero nominal floors worsened at `none` (roll ss_error IMPROVED 0.539 -> 0.428 deg); `fault_severity` reach 7.70% vs ArmA 7.71% -> **Lane-2 curriculum-tax hypothesis refuted**. Rule ambiguity recorded: rule-1 uses `|d|` notation but the H2 branch is degradation-only (PLAN 583-585 defines the floor as a REAL-vs-NULL significance test), so the floor-clearing IMPROVEMENT does not fire H2 -- affirmed by independent review. Report `analysis/diagnose-20260728-004710/report.md`; independent `report-reviewer` 2 rounds (both REVISE on grammar/numeric/scope defects, verdict + interpretive call + all 17 advantage figures AFFIRMED in both); gates `report-review` approve + `report-coverage` 7/7 groups 49/49 tokens 9/9 sections stamped. Caveats: single-seed (seed 30) screening, never a paper number (11.6 item 5); run STITCHED across the resume (DORAEMON state restored -- `fault_severity` resumes mid-curriculum at 0.0178, not 0.0 -- but the env RNG stream restarted at 2350); yaw is the weakest axis (3.01x vs ArmA 4.00x at `none`, corroborated by `Reward/yaw_vel` and by `none` yaw `os_env_mean` +1.34 pp, the largest of 13 sub-floor worsened cells in a 68-cell exhaustive scan) | workstation, DONE (~3 h resume + ~3.3 h pre-crash) | **student track OPEN against this teacher** -> C4 distillation + E-obs |
| HydroRC | hydro DR nominals recentered to the Stonefish-measured effective values (marinelab `exp/hydro-recenter` 016d1b1; proposal `next-20260727-174905`). **READOUT 2026-07-28: Isaac paired gate FAIL -- recenter NOT adopted, Stonefish readout not entered (pre-registered rule).** Run `trpo_hydrorc_s30_260728_013136` completed 5000/5000 clean (final reward 260.38 vs E-int true final 263.98). Gate (paired vs E-int, none, bound 16.8%, degradation-only): roll ss_error +1.9% within, pitch ss_error -15.7% improve, yaw ss_error **+18.8% BREACH** (degrades at all levels +18.8/+23.4/+24.3/+31.8%), roll n_gt20 **0 -> 18.67 envs BREACH** (clears the 11.6 REAL floor 15 envs; roll os_env_mean 8.18 -> 17.96 pp corroborates). Structure: DC intact at none, regression is the step-transient tail at ALL DR levels; E-int had closed the family roll-transient band (17-21 pp historical) to 8.18 pp and HydroRC returns to 17.96 pp -- passive damping is now the leading candidate for the previously UNEXPLAINED roll-transient inversion (wiki roll_transient page). `hard` collapses broadly (att_norm 1.691 vs 0.719 deg, survival 96.9 vs 100.0, first sub-100 in family -- relative band around a 10-100x lower nominal makes the hard corner near-undamped). Supplementary m4-dead: fault delta 7-17x LARGER than E-int at every level despite MORE fault-curriculum reach (10.83% vs 7.70%) -- fault tolerance and plant damping are coupled. thruster_util J_C/d_k 0.805 (back at anchor level). Report `analysis/diagnose-20260728-081953/report.md`; report-review approve + coverage 7/7 groups 49/49 tokens 9/9 sections stamped; independent reviewer 2 rounds (R1 REVISE: E-int final-reward referent 260.5 -> 263.98 + segment disambiguation, fixed by re-authoring; R2 APPROVE 0 findings). NEXT (human decision, nothing queued): run P1 cross-sim joint1 swing FIRST (zero GPU, Stonefish machine) to measure the deployment sim's closed-loop rotational damping, THEN pick the recenter-v2 arm -- (a) translational+heave-only (loses Lane-2 power on the rotational limit-cycle axes), (b) rotational recenter + raised DR lower-corner floor (second variable), (c) log-mean rotational recenter (arbitrary without P1). E-int remains the final teacher; the Stonefish limit-cycle Lane-2-vs-Lane-1 question stays OPEN. Branch `exp/hydro-recenter` kept as the v2 base; marinelab parked back on `exp/max-thrust-dr` | workstation GPU0, DONE (~5.8 h train + 2x ~8 min eval) | Isaac gate FAIL -> Stonefish diagnostic NOT entered; P1 before any v2 |
| E-obs | student observability retrain: +velocity (heave-first) obs channel +/- longer TCN history, WITH-vs-WITHOUT A/B, deterministic encoder (carries `closed_loop_latent_collapse` + `on_policy_dagger` handoff). **DEFERRED 2026-07-27 (user): teacher-first** — the student track (E-obs and the C4 pack) starts only AFTER the final teacher baseline exists, and distills from THAT teacher (E-int output), not the buoyfix anchor | DGX (cuDNN works; distillation is machine-isolation-exempt, section 8) — after E-int | E4 in-loop latent env-var reconstruction ratio vs the 8-16% collapse baseline |
| E-lat | latency-DR — REMOTIVATED: blocker 1 (eval instrument) resolved 2026-07-24; blocker 2 (off-DORAEMON stall) now has a validated template = the `fault_severity` nominal-0 DORAEMON-dim pattern (mode 0.00, no stall, FaultDR-AB). Precondition: the anchor delay-sweep verdict from the Z4 instrument | workstation | error-vs-delay response, then a DR arm only if the sweep shows fragility |
| E-t200 | ~~thruster nonlinear curve / deadband~~ **CORRECTED 2026-07-27: DEFER behind a bench measurement** — the wiki page's own 2026-07-02 decision is keep `enable_thrust_curve=False` until the real command->thrust curve is bench-measured; the curve is a PLANT MODEL (not a DR perturbation), and an unverified curve can manufacture a worse plant gap than the known linear one. The backlog's "unblocked" field overstates it; roster entry 12.2 as first written repeated that overstatement | — | bench-measure first, then re-propose |

Sequencing (REVISED 2026-07-27, user: teacher-first): finalize the TEACHER first, then
optimize the student against that baseline. Order = E-int (final teacher; E-ftc1 only if
the user revives it first) -> C4 distillation + E-obs A/B on the E-int teacher -> E-lat
(sweep first). E-t200 deferred behind a bench measurement (corrected row above). The
earlier "E-obs runs in parallel" note is SUPERSEDED — the student track is serialized
behind the final teacher by user decision. Two-machine split explicit: workstation =
E-int (campaign-compared); DGX = idle-by-decision until the student track opens (then
hosts distillation/E-obs); Stonefish machine = P1/yaw diagnostic (handoff pack delivered
2026-07-27, in motion).

### 12.3 Zero-GPU work

- B0c formal exp-analyze report: **DONE 2026-07-27** — `analysis/diagnose-20260727-151917`
  (13 findings, coverage 7/7 + cross-run refs green, independent review: revise -> fixes
  verified -> approve). NULL-on-nominal reproduced on the section-7 pairing and robust to
  the anchor-eval choice; watch items for E-int: pitch hard DC/CV, thruster_util binding
  0.805->0.853, cost-critic +25% (priv-obs-invisible parameter).
- Ledger hygiene: mark FTC-m4 / FaultDR-AB proposal outcomes in the `teacher_baseline_buoyfix`
  plan (both still `derived_status: planned`) and attach the `fault_dr` campaign to this program.

### 12.4 Backlog reconciliation (13 live leads, re-checked 2026-07-27)

| lead | disposition |
|:--|:--|
| `closed_loop_latent_collapse...` | CARRY -> E-obs |
| `on_policy_dagger...` | fold into E-obs (page's own handoff) |
| `experiment_idea_latency...` | CARRY -> E-lat (remotivated, see 12.2) |
| `thruster_nonlinear_curve_t200...` | CARRY -> E-t200 (unblocked) |
| `curriculum_recalibration...` | unchanged: B0b behind the 8k+ edge; TAM-arm span unsourced |
| `roll_transient_...none_dr...` | DEFER behind C3 (unchanged, 11.7) |
| `stonefish_yaw_gap...` (P1) | Stonefish half **DONE 2026-07-29** (all 6 cases); the Isaac-side replay is the only remaining half -> roster row **P1-isaac** in 12.2, script staged and source-verified |
| `joint1_stage_1_gate...` | DEFER (prerequisite checkpoint absent) |
| `reward_sigma_integral_obs_gate...` | DEFER (R1 not in code, no consumer) |
| `container_cudnn_is_cu13...` | = gate D-c |
| `imu_45deg_offset...` | DEFER (robot bring-up, user 2026-07-20) |
| `sim_hydro_nominal...` | max_thrust half = gate D-a; TAM moment-arm cannot-close |
| `tam_vertical_single_motor...` | DEFER (m4 HW fault); consequence: fault eval stays m4-only, vertical-fault fidelity blocked |

C3 (paper phase), B0b/B2 (8k+ edge) and the section-9 cannot-close list are unchanged.
No proposal artifacts were written for 12.2 — each candidate gets its lint-clean
`next-*` proposal (exp-design, independent review) only when the human picks it.
