---
title: "Baseline open experiment-leads backlog (beyond heavy-tail): triage by value x launchability with blockers"
tags: ["backlog", "experiment-roster", "next-experiment", "heavy-tail", "doraemon-per-axis-gate", "command-box", "tam-dr", "sim-to-real", "triage", "teacher-baseline", "doraemon", "performance_lb", "exploration", "batch-planning", "needs-apply-before-retrain", "plant-fidelity", "dgx", "correction", "joint1"]
created: 2026-07-14T07:57:24.357274
updated: 2026-07-23T06:37:45.059552
sources: ["diagnose-20260713-081707", "diagnose-20260715-133249", "diagnose-20260720-124259", "diagnose-20260713-031533"]
links: ["decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema.md", "april_2026_entropy_collapse_campaign_machinery_bug_solved_conver.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
blocked-on: "PARKED BY USER DECISION 2026-07-20: all open leads (roster A + B) are to be planned and executed in ONE later batch pass; nothing is to be launched before that pass"
---

# Baseline open experiment-leads backlog (beyond heavy-tail): triage by value x launchability with blockers

Consolidated index of the baseline's open experiment leads that are NOT the hard-DR roll heavy-tail
(the one weakness the p7_tail campaign targeted). Created because these WERE surfaced by the p7-planning
broad audit (recorded in DESIGN.p7_tail.md "Post-audit gaps", 2026-07-13) but were then DROPPED from the
campaign README's "미해결/다음" summary, which flattened the picture to "유일한 약점 = heavy-tail". This page
is the searchable backlog so a broad query reliably surfaces the full experiment roster, not just the
heavy-tail thread. Reference baseline: trpo_baseline_260713_031325 (consolidated main 7ac39c8).

## Triage: experiment value x launchable-now, with blocker

| Lead | Value | Launchable now? | Blocker / prerequisite | Priority |
|---|---|---|---|---|
| Eval command-box extension (static eval steps only to ATT_AMP=15 deg while trained box = +-30 deg -> inner half only) | HIGH — corrects tail MEASUREMENT itself | YES, zero-GPU, no retrain (re-eval existing checkpoints over full box) | none | 1 (nearly free) |
| DORAEMON per-axis success-gate (single binding axis=roll drives a GLOBAL min-gate freezing ALL strong-axis DR widening; set_axis_gate/_AXIS_PARAM_GATE do NOT exist) | HIGH — DIRECT structural fix for the e1 stall; unblocks the whole class of reward-costly probes | NO | engine code in marinelab/algorithms/doraemon.py | 2 (max structural lever) |
| performance_lb recalibration (lb=250 sits on baseline return ~247 -> ANY intervention costing ~10% return stalls the curriculum; e1 proved it) | MED-HIGH | partial (after measurement) | measure delayed-nominal return first; decide relative vs absolute lb | 2 (paired with per-axis gate) |
| Latency as a DORAEMON _PARAM_DEFS dim (e1 redesign; ties to real-robot vibration channel B) | MED-HIGH | NO | engine code (make control_delay a curriculum dim) | 3 |
| TAM / max_thrust DR band (the ONLY axis with NO DR at all; a wrong TAM is a systematic bias hitting all envs identically; onboard IMU+pressure, no load cell -> CANNOT be measured) | HIGH (deployment) | NO | source a physically-defensible numeric band from spec/literature (not measurable) | 3 (design-first) |
| thruster nonlinear curve ON (real T200 deadband + signed-square that multiplicative DR can NEVER reproduce) | conditional | NO | bench-measure real command->thrust first; an unverified curve manufactures a new sim-to-real gap | wait (measure before enabling) |
| hydro nominal measurement/anchoring (sim nominal is ANALYTICAL not measured; the "low-damping envs are hard" tail story rests on a possibly mis-anchored nominal) | MED | NO | tank free-decay protocol; and free-decay is non-separable (GM/I/A lumped) so only partial | wait |
| state_dependent_std, z-conditioned variant (feed DR-carrying encoder latent to the std head) | MED | NO | eval npz must log raw obs std (engine gap); premise weakened since baseline already converges to tight std 0.109 | parked, re-rank after tail probes |
| constraint inert-2 loosening ablation (rp_vel_settling + manipulability are the ONLY 2 genuinely inert of 10; other 8 shaped early training) | LOW | YES (budgets x100 on those 2) | none | low (deprioritized; slack is healthy complementary slackness, not a defect) |

## Not experiments (recorded so they are not mistaken for launchable probes)

- Real-robot vibration channel PICK (A obs-noise / B latency / D control-rate): needs REAL FFT logs to choose the channel; cannot design the training experiment without them.
- Real-robot vibration channel C (clamp-saturation blind spot): ALREADY largely closed by data, not a new experiment — baseline clip_fraction=0.0048 (P4 logging) means |a|>=1 saturation is ~0, so the smoothness-reward blind-spot is an unlikely vibration cause (rules/03: evidence over guess).
- arm step-response ID (Dynamixel bus telemetry), net buoyancy (pressure): MEASUREMENTS, not RL experiments; the only sim-to-real targets actually reachable with the current sensor suite.

## Movable-now recommendation

Of everything above, only two are both high-value and unblocked today: (1) command-box extension eval (zero-GPU; without it the whole heavy-tail success/failure judgment is made on the inner half of the trained envelope), and (2) DORAEMON per-axis gate / lb recalibration (engine code, but it unblocks every future return-costly probe that currently stalls like e1). The sim-to-real gaps (TAM DR, thruster curve, hydro) may matter MORE than heavy-tail for real deployment but are design-first / measurement-gated, not launchable now. Formalize any chosen lead through exp-design (single variable, H1/H2 discriminator, human-gated launch); do NOT auto-launch.

---

## Update (2026-07-14T09:56:26.815912)

Flagged needs-experiment 2026-07-14: this is the open experiment-leads backlog (command-box eval, DORAEMON per-axis gate, latency-as-DR-dim, state_std z-cond, etc.). Soft actionable -- every next-experiment/summary pass must enumerate these leads (omx wiki list --status needs-experiment) and carry or explicitly defer them, so the heavy-tail-flatten drop cannot recur.

---

## Update (2026-07-15T04:54:42.574431)

## Update (2026-07-15): two leads dispositioned + a NEW lead surfaced

- **Eval command-box extension (Priority 1): DONE** this session (commit 8c07584 — ATT_AMP 15->30 deg, YAW_RATE 0.25->0.5; eval box now matches trained +-30 deg box). Lead closed.
- **performance_lb recalibration (Priority 2): DONE** via probe trpo_perflb200_260715_023744 (analysis diagnose-20260715-133249). Result: lowering performance_lb 250->200 UN-STALLS the curriculum (mode -2->0, success 0.407->0.712, ess 0.414->0.754, DR widens) — confirms the 'lb sits on baseline return, so any return-costly intervention stalls' diagnosis. **DECISION: adopt performance_lb=200 as the standing setting.** Lead closed.
- **NEW lead surfaced (was hidden behind the stall): exploration-machinery collapse.** The SAME probe proved the actor entropy/noise_std collapse (entropy ~-7.8, noise_std pinned near min_std=0.05 floor) is CAUSALLY INDEPENDENT of the DORAEMON gate — its trajectory is near-identical (max dev 0.18 entropy / 0.003 noise_std) whether the curriculum stalls or not. So neither performance_lb NOR the DORAEMON per-axis gate will fix exploration. The next exploration lever must target the actor noise/entropy machinery directly: min_std (0.05 floor), entropy_coef (0.003), or the noise parameterization / entropy schedule. See finding 'performance_lb (DORAEMON gate) is causally independent of the actor exploration collapse'.

STILL OPEN (unchanged): DORAEMON per-axis success-gate (max structural lever, blocked on marinelab/algorithms/doraemon.py engine code) — note it addresses per-axis DR WIDENING, NOT the exploration collapse above; latency-as-DR-dim (engine code); TAM/max_thrust DR band (design-first, needs-apply-before-retrain); thruster nonlinear curve (measure-first); hydro nominal anchoring (measure-first); state_std z-conditioned (parked); constraint inert-2 (low).

---

## Update (2026-07-20T03:15:55.121613)

## Audit re-scope (2026-07-20, backlog audit)

STILL OPEN as a live index -- this is a real backlog, not a stale page. Verified state: 2 of 9 sub-leads
are closed (command-box eval extension shipped, commit 8c07584; performance_lb probe run
`trpo_perflb200_260715_023744` -- but note its verdict was later reversed to lb=250, see
[[decision_do_not_adopt_performance_lb_200_on_the_adopted_bias_ema]]). The other 7 were independently
re-verified as genuinely unimplemented: no per-axis DORAEMON gate in
`marinelab/algorithms/doraemon.py`, and no run or page exists for latency-as-DR-dim, TAM/max_thrust DR
band sourcing, thruster-curve bench measurement, or hydro free-decay measurement.

HOUSEKEEPING: the exploration/entropy-collapse lead recorded in this page's own 2026-07-15 update
(min_std=0.05 floor, entropy_coef=0.003, shown causally independent of the DORAEMON gate) is not yet
folded into the triage table -- add it as item 10 when this page is next touched.

---

## Update (2026-07-20T04:48:10.764929)

## Batch-execution decision + full open roster (2026-07-20, user decision)

USER DECISION (2026-07-20): do NOT launch any of these now. Everything below is parked and
will be planned and executed in ONE later pass, so that the ordering is chosen against the
full picture instead of run-by-run. Nothing in this update was launched. This supersedes any
"movable-now recommendation" above as the CURRENT operating instruction -- those rankings
remain valid as analysis, but the execution trigger is the later batch pass.

Phase context that governs the whole roster: the project is in a SETTINGS-SEARCH phase --
many cheap short runs to settle the configuration. The small `max_iterations` is DELIBERATE,
not a defect. The real training run happens later on an NVIDIA DGX with much larger
`max_iterations` AND `num_envs`. So "run it longer" is never the answer in this phase, and the
plant-fidelity items in roster B matter most immediately BEFORE that scale-up.

### Two rosters, do not confuse them

- **Roster A/B below = the status-TAGGED wiki pages** (`omx wiki list --status ...`). These are
  what the per-turn backlog injection enumerates.
- **The triage table earlier in THIS page = sub-leads**, several of which have no page of their
  own (per-axis DORAEMON gate, latency-as-DR-dim, state_std z-conditioned, constraint inert-2,
  exploration collapse). They are still open and are NOT visible to a `--status` query. A batch
  planning pass must read BOTH.

### Roster A -- `needs-experiment` (10 pages), by what each actually costs

| Lead | Costs | Blocked on |
|---|---|---|
| `step_interval_250_400_probe...` | 1 training run (8000 it) | nothing -- reviewer-APPROVED, awaiting human go |
| `thruster_nonlinear_curve_t200...` | training + bench measurement first | real command->thrust bench data |
| `joint1_stage_1_gate_go...` | training (separate arm-drift track) | nothing technical |
| `cross_run_dr_comparability...` | EVAL ONLY, zero training | nothing -- cheapest open item |
| `extend8k_saturated_the_dr_config_box...` | analysis -> then a config change | needs the P-A6 physical-span review (measured hardware variation vs current bounds) |
| `penalty_vs_objective_exchange_rate...` | analysis only | nothing |
| `literature_map_...steady_state_error` | reading only, no GPU | nothing |
| `e3_s_5000_iter_budget_verdict...` | -- | same-plant half ANSWERED; only the DGX-scale arm remains, deferred to the DGX phase |
| `stonefish_yaw_gap_claim_review...` | investigation | its own P1 (cross-sim joint1 swing) + P2 (eval yaw-torque sweep) pre-checks |
| `baseline_open_experiment_leads_backlog...` | -- | this page; an index, not a probe |

### Roster B -- `needs-apply-before-retrain` (4 pages): plant fidelity, gates the DGX run

These are places where the SIMULATOR DISAGREES WITH THE MEASURED ROBOT. They do not block the
current settings-search campaign (every run shares the same known-imperfect plant, so
within-campaign comparisons stay valid), but a large DGX run on an uncorrected plant would
train against the wrong dynamics. Each is blocked on a measurement or a human decision, not on
compute:

| Gate | Blocked on |
|---|---|
| `imu_45deg_offset_pitch_negation...` | 3DM-GX5 datasheet decision (FLU/NED convention vs chip quirk); firmware sign already reconciled |
| `tam_vertical_single_motor_dual_esc...` | m4 remeasurement (HW fault) + full B1 vertical translation |
| `sim_hydro_nominal_is_analytical_not_measured...` | sourcing a defensible TAM moment-arm / max_thrust DR band (no load cell available) |
| `plant_fix...main_hull_volume_0_009...` | user decisions (1) is the paper's ||F_bu||=1.835 kgf buoy-net or total-displacement, (2) run_group naming -- DEFERRED to the next-gen plant refresh by user decision 2026-07-16 |

### HOUSEKEEPING discharged: exploration collapse is now item 10

The 2026-07-15 update surfaced it and the 2026-07-20 audit flagged that it was never folded into
the triage table. Recording it here as the table's item 10 so it stops being invisible:

- **Item 10 -- actor exploration-machinery collapse.** Actor entropy ~-7.8 and `noise_std` pinned
  near the `min_std=0.05` floor, proven CAUSALLY INDEPENDENT of the DORAEMON gate (near-identical
  trajectory whether the curriculum stalls or not). Value: MED-HIGH. Launchable: yes in principle
  (a config probe on `min_std` / `entropy_coef` / the noise parameterization), but it must go
  through exp-design as a single-variable H1/H2 probe like any other. No blocker other than the
  batch-pass decision.

### Suggested ordering for the later batch pass (a starting point, not a commitment)

1. **Zero-GPU first** -- cross-run comparability re-eval, penalty-vs-objective exchange rate,
   literature map. These change what the other experiments MEAN, and cost no compute.
2. **One training probe at a time** (single-variable rule) -- the approved `step_interval` probe
   is the only one currently formalized with H1/H2 predictions and a manipulation check.
3. **Plant fidelity (roster B) before the DGX scale-up** -- these need user decisions and
   measurements, so start them early even though they are not compute-bound.
4. Whatever is chosen, formalize through exp-design (single variable, H1/H2 discriminator) and
   keep the launch human-gated. Do NOT auto-launch.

---

## Update (2026-07-20T04:48:46.103705)

## CORRECTION to the roster-A table above (2026-07-20, same session)

The `joint1_stage_1_gate_go...` row was written as "training (separate arm-drift track), blocked
on nothing technical". That is WRONG and would mislead the batch pass into queueing a training
run. Verified against the page itself:

- Stage 1 is a GATE that already returned **GO** (drift is real on unlimited physics, refuting the
  wall-artifact lane). It is not an experiment waiting to run.
- The page explicitly says **"CAVEATS gating Stage 2 (do NOT auto-proceed)"**. The immediate next
  step is a RE-MEASUREMENT, not training: the old 260525 teacher fast-fails on the new physics
  under flat target (failing-env median time-to-failure 7-10 s at every DR level), so most
  observation windows are truncated -- drift must be re-measured on a policy that actually
  station-keeps on unlimited physics.
- Stage 2 additionally needs its OWN baseline drift measurement, because its ee-action base
  overwrites `_joint_pos_targets` with IK output wrapping to (-pi, pi] (`albc_env.py:579`,
  `kinematics.py:213-214`) -- a different command signal than the direct joint-delta action this
  gate measured. This gate confirmed the PREMISE, not the ee-action magnitude.
- Dimension note carried so the batch pass does not trip on it: that teacher is full-DOF
  (87D obs / 24D priv / 8D action / latent 9) -- run it on `Isaac-ConstrainedALBC-Full-TRPO-v0`,
  NOT the attitude-only main task (69D/28D).

Corrected row: **cost = eval/re-measurement (zero training); blocker = needs a station-keeping
policy on unlimited physics to measure against.**

Method note for whoever picks this up: use PEAK excursion (max |theta_cum| over the pre-term
window), never endpoint -- endpoint under-counts because many command trajectories ramp past 2pi
and then reverse.

---

## Update (2026-07-20T04:50:14.529097)

## CORRECTION 2 to the roster-A table (2026-07-20, same session) -- the "cheap zero-GPU tier" does not exist

Four more rows were wrong, all in the SAME direction, and the suggested ordering built on them is
RETRACTED. Verified by reading each page in full.

**The systematic error:** these pages' TITLES state a finding ("all four penalties together buy
only 0.125 deg", "nobody has eliminated steady-state error", "--doraemon-dr-from already provides
a common test distribution"), so they read like COMPLETED analyses. They are not. In each case the
analysis IS done and that is precisely why the page is tagged `needs-experiment`: the finding
MOTIVATES an experiment that has not been run. A page's remaining work cannot be inferred from its
title -- read its "next experiment / lead" section.

| Lead | What I wrongly wrote | What the page actually says |
|---|---|---|
| `cross_run_dr_comparability...` | "EVAL ONLY, zero training, cheapest open item" | The shared-exam eval was ALREADY run once (P-B1 vs baseline). Remaining = a TRAINING arm: the curriculum-replay probe (`CurriculumReplayer` + `--replay_curriculum_path`) to separate measurement-confound from training-confound. No run or report uses it for this discrimination yet. |
| `penalty_vs_objective_exchange_rate...` | "analysis only, blocked on nothing" | Analysis done. Remaining = a penalty-RESCALING training experiment, and it is GATED by an unresolved counter-argument the page states explicitly: it "needs a measured deficiency as its motivation ... Without that, it is the 'generic solution without evidence' anti-pattern." |
| `literature_map_...steady_state_error` | "reading only, no GPU" | The reading is done. The page carries FOUR concrete unstarted actions. Lead 1 is a CODE change re-verified as not done: decouple the `_bias_ema` update from the `k_bias` gate (`envs/main/config.py:626` still raises), then run the k_bias=0 vs -2.0 ablation. Also two-scale kernel / L1-Huber experiments. |
| `extend8k_saturated_the_dr_config_box...` | "analysis -> config change, blocked on the P-A6 physical-span review" | "P-A6 physical-span review" is real (verbatim in the page), but it is a JUSTIFICATION CONDITION, not a tracked blocking dependency, and the shape is a BRANCH not a line: either (a) widen the configured DR bounds -- justified only where MEASURED hardware variation exceeds them -- or (b) pursue plant fidelity instead. Nothing formally blocks it; what is missing is evidence. |

**RETRACTED: the "zero-GPU first" ordering.** It rested on the three rows above being analysis-only.
With them corrected there is no meaningful zero-GPU tier left in roster A. The genuinely cheapest
UNBLOCKED item is now the small CODE change in the literature-map lead (decouple `_bias_ema` from
`k_bias`), which is unstarted and unblocked but is implementation, not free reading -- and it only
pays off once its ablation is actually run.

**Implication for the batch pass:** roster A is heavier than the earlier table implied. Nearly every
open lead terminates in a training run, so the batch pass is mainly an ORDERING problem over
training runs under a one-variable-at-a-time constraint -- not a "clear the cheap ones first" sweep.
Budget accordingly.

---

## Update (2026-07-20T06:09:23.834087)

## CORRECTION to item 10 (actor exploration-machinery collapse), 2026-07-20

Item 10 above names `min_std` (0.05) as a candidate config probe. That lever is INVALID and must
not be queued as written:

1. The scalar `min_std` is dead code here -- `constraint_trpo.py:507-511` takes the per-dim branch
   whenever `min_std_per_dim` is set, and it is set (`rsl_rl_ppo_cfg.py:246` = arm 0.10 /
   thruster 0.05). Raising the scalar would be a no-op and would return a meaningless null.
2. min_std was already shown not to bind: commit `26b2f54` (04-21) states "thruster std 0.22-0.34
   (4-6x above min_std floor 0.05) ... min_std was NOT binding; per-dim entropy IS". A dedicated
   probe run also exists in the legacy tree (`r10_thr_minstd`, 04-19).

Item 10 also treats the collapse as an un-investigated new lead. It is not: a 49-run campaign
(2026-03-27~04-22) fixed the machinery bug (log_std outside the trust region, `3132605`) and
shipped per-dim entropy_coef / per-dim min_std, then closed with "universal entropy collapse"
still recorded as unresolved. Adaptive entropy and ERC-TRPO were tried and reverted; raising
entropy_coef to fight collapse was tried pre-campaign and worsened roll. Read
[[april_2026_entropy_collapse_campaign_machinery_bug_solved_conver]] BEFORE designing any
exploration probe -- the only live single variable is `entropy_coef_per_dim` (thruster leg), and
it must be weighed against the documented opposite failure (roll limit cycle).

Cheapest next step for this item is zero-GPU: read PER-DIM log_std from an extend8k checkpoint to
establish which dims are actually floor-bound. `Policy/mean_noise_std` is an 8-dim mean and cannot
answer that. Park status unchanged.

---

## Update (2026-07-23T06:37:45.059552)

CLOSED 2026-07-23 (plan consolidation): index page discharged -- every sub-lead is now carried, deferred-with-edge, or closed in docs/reference/teacher-campaign-plan.md (sections 5-6) and the per-lead wiki statuses. The 2026-07-20 park order ('one batch pass') is fulfilled by that consolidation.
