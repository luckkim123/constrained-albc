# Backlog closeout — final report

**Program**: `backlog-closeout`. **Authority**: the user's 2026-08-05 00:24 KST grant to clear the
whole ledger without per-item approval, deadline 2026-08-05 24:00 KST.
**Definition of done**: `omx wiki list --status needs-experiment` and
`--status needs-apply-before-retrain` both return zero rows. Not "the campaign concluded".

> **STATUS: FINAL — 2026-08-05 16:45 KST.** Both closing queries return zero rows; see section 6.

---

## 1. Result

**17 leads in, 17 closed.** Both `needs-experiment` and `needs-apply-before-retrain` return zero
rows. Nothing was closed by declaring it finished: every one of the 17 carries a verdict, the
evidence behind it, and the commit that recorded it.

Two of the three "plant is wrong, apply before any retrain" blockers turned out to be **real model
errors that the policy is measurably insensitive to** — which is a different and more useful answer
than either "fixed" or "still open". They are accepted for gen-1 with the error documented, rather
than applied, because applying them would have voided E-int as the DGX flagship's baseline.

Three findings came out larger than the leads that produced them, and the first two are corrections
to things the workspace already believed:

- **No 5000-iteration teacher on this plant ever reached its DR ceiling.** E-int — the shipped
  teacher, the DGX baseline, and every student's source — ended with **0 of 21 DORAEMON dims at
  Beta(1,1)** and 65 % of its KL budget spent. Saturation is at iteration **7748**.
- **The `hard` column of the recorded 2026-07-24 Z4 latency sweep was never a paired comparison.**
  An injection that draws from the RNG shifts every subsequent DR draw, so `d=0` and `d>=1` are not
  the same envs. The `none` column stands; the rest was corrected in place.
- **The integral-gate threshold is at its optimum, not inert.** The R6 sweep was expected to return
  a flat null in both directions. Widening did. Narrowing did not: it is actively harmful, taking
  roll `n_gt20` from 0 to 42 of 64 envs at `none`, and the ungated bias-EMA path that justified the
  null expectation does not compensate for it. A knob confirmed to sit at an optimum is a stronger
  result than a knob confirmed to do nothing.

## 2. The ledger — all 17

Verdict vocabulary: **RESOLVED** (answered with evidence), **CLOSED-NULL** (ran, no effect),
**CLOSED-OUT-OF-SCOPE** (the question does not bear on the gen-1 deliverable),
**DEFERRED-HARDWARE** (needs a physical measurement the user removed from the queue on 2026-08-05).

### Closed by verdict, no GPU (9) — commit `8b63074`

| Lead | Verdict | Basis |
|:--|:--|:--|
| `stonefish_yaw_gap_claim_review…` | CLOSED-OUT-OF-SCOPE | Purpose was Isaac↔Stonefish alignment; Stonefish dropped by user decision. |
| `thruster_static_gain_gap…` | CLOSED-OUT-OF-SCOPE | The gap was Stonefish-vs-Isaac; with one side gone there is no comparison. Residual Isaac-side question needs the T200 bench → hardware. |
| `stonefish_rotational_drag…` | CLOSED-OUT-OF-SCOPE | Stonefish-side mesh question. The Isaac-side damping half survives inside the HydroRC lead, not duplicated here. |
| `thruster_nonlinear_curve_t200…` | DEFERRED-HARDWARE | Its own 2026-07-02 decision holds `enable_thrust_curve=False` until measured. |
| `imu_45deg_offset…` | DEFERRED-HARDWARE | Already deferred 2026-07-20 pending a real-robot convention check; zero sim-side impact meanwhile. |
| `tam_vertical…` | DEFERRED-HARDWARE | Blocked on m4 remeasurement, which is a hardware fault. |
| `sim_hydro_nominal…` | DEFERRED-HARDWARE | Only the TAM moment-arm band remains and it needs a CAD/bracket source; the max_thrust half closed 2026-07-27. |
| `c4b_dagger_correction…` | CLOSED-NULL | Ran 2026-08-03, missed the GO bar by 0.0247 (2.54σ) while costing +0.1401 deg hard roll. Phase D and X1 both ran after it and neither rescued it. |
| `joint1_stage_1_gate…` (Stage 2) | CLOSED-OUT-OF-SCOPE | Needs a prerequisite station-keeping policy on unlimited joint1 physics; the shipped task is attitude-only so arm drift does not bound the deliverable. Stage 1's verdict stands as the durable result. |

### Closed on evidence already in hand (2) — commit `e4231f3`

| Lead | Verdict | Basis |
|:--|:--|:--|
| `roll_transient…` (nominal-corner exposure) | RESOLVED | The inverted transient reproduces across runs and campaigns; it is a property of the plant, not of a DR sampling floor, so the proposed floor probe would not have discriminated. |
| `the_obs76_teacher…` (distillation gap) | CLOSED-OUT-OF-SCOPE | All five measured students land at 2.5–3.1 deg hard roll dispersion regardless of teacher. The ceiling is the distillation step, so no student arm on this teacher could move the deliverable. |

### Plant errors — measured, not applied (3) — commits `598db89`, `ee3bcac`

These were the `needs-apply-before-retrain` blockers. The plan's instruction was *do not blindly
apply*: applying changes the plant and voids E-int as the flagship's baseline. So each was tested by
evaluating E-int's own checkpoint under the corrected value against the current one, same DORAEMON
anchor, and judged against the decision floors.

| Lead | Verdict | Basis |
|:--|:--|:--|
| `buoy_added_mass…` | RESOLVED, accepted for gen-1 | Corrected geometric values produced **zero REAL flags**. A third point at the representable ceiling moved survival by −18.75 to −31.25 pp, so its accuracy deltas are survivorship-contaminated and were excluded rather than quoted. Known model error, policy insensitive. |
| `hydrorc_016d1b1…` | RESOLVED, accepted for gen-1 | Yaw damping swept ×0.1 and ×10 — a two-decade bracket — produced **zero REAL flags** at either end. |
| `hydrorc_is_half_recentered…` | RESOLVED-BY the above | Subsumed once Stonefish left its blocker list; no third eval run. |

### Closed on this program's own runs (2) — commits `567732f`, `e2ada17`

| Lead | Verdict | Basis |
|:--|:--|:--|
| `experiment_idea_latency…` | CLOSED-OUT-OF-SCOPE for gen-1, carried as a gen-2 requirement | Measured E-int's delay response (below). Training the delay in needs either a curriculum-engine change or a measured `performance_lb` recalibration — two of three committed GPU0 slots, unvalidatable before the deadline. A naive delay-ON run reproduces `trpo_e1_latdr` and answers nothing. The full recipe is recorded so gen-2 starts from it. |
| `curriculum_recalibration_protocol…` | RESOLVED; Step 1 DEFERRED-HARDWARE | Run A (below). Its 2026-07-21 premise — runs at this length are box-exhausted, so bounds-widening is the only lever — is false on the current plant. |

### Closed on the R6 three-point sweep (1) — this session

| Lead | Verdict | Basis |
|:--|:--|:--|
| `reward_sigma…` (R6 integral-gate threshold) | **CLOSED-NULL**; default confirmed at its optimum | Runs B and C below. Both arms null under the pre-registered rule, so `(0.10, 0.10, 0.10)` stands — but the default also beats both probes on roll `n_gt20` at all four DR levels, so the knob is at an optimum rather than inert. |

## 3. Runs

### Run A — iteration budget (`trpo_iterbudget_s30_260805_012813`) — DONE

E-int resumed 4999 → 9998, nothing changed but the budget, to re-run the curriculum lead's Step 0 on
the plant we ship rather than the retired posttam one.

| | E-int at 5000 | Run A at 9998 |
|:--|:--|:--|
| dims at Beta(1,1) | **0 of 21** | **21 of 21** |
| KL budget spent | 2.2800 | 3.5209 |
| expansions | 19 | 30 |
| saturation iteration | — | **7748** |

29 of the 30 chain expansions sat exactly at the `kl_ub` = 0.12 cap; the 30th was a partial 0.0410
step onto the ceiling. After 7748, nine further boundaries fired with `mode` = 0 and `kl_step` = 0 —
the scheduler kept deciding "expand" with nothing left to expand into, which is what distinguishes
saturation from a stall mechanically. `DORAEMON/entropy_before` took exactly two distinct values over
the 2250 frozen iterations, reproducing the extend8k signature.

The four dims whose nominal is 0 were the least expanded at 5000: `payload_cog_offset_xy_u`
Beta(1, 7.288), `ocean_current_strength` Beta(1, 7.670), `obs_noise_scale` Beta(1, 7.918),
`fault_severity` Beta(1, 10.099) — a mean of 9 % of its declared range. A run launched with
`fault.enable=True` therefore experienced very little fault.

This does **not** invalidate teacher-vs-teacher verdicts at 5000: every arm stops at about the same
budget fraction, so the exams were comparable. It does mean no run at that length supports a claim of
robustness to the *declared* box.

### Run B — R6 integral-gate widen arm (`trpo_gate020_s30_260805_063110`) — NULL

Launched 06:31:05 with a 95-second GPU0 gap after Run A, via an armed handoff, and verified at
06:35:05 by reading `integral_gate_threshold` = (0.2, 0.2, 0.2) and `fault.enable: true` back out of
the run's own recorded `params/env.yaml` — a check this program added after the control-delay sweep
proved an override can be accepted, exit 0, and inject nothing. Finished 4999/5000 at 11:26:33.

**Pairing checked before any number was read**, because the decision floors declare themselves
"paired same-machine": 23 of 23 per-env draw arrays elementwise identical at all four DR levels,
against both E-int baselines (which are themselves mutually paired, so the DESIGN-named GPU0 one and
the same-device GPU1 one are interchangeable — the verdict run against both differs only in the
fourth decimal). Survival 100 % at every level in both arms, so nothing is contaminated.

**§5 clause 1 fails and decides the verdict.** It requires `ss_error` to IMPROVE past the 0.10 deg
floor on at least 2 of 4 levels. There are zero improvements and six REAL regressions — pitch and
`att_norm` at soft, medium and hard, +0.12 to +0.21 deg. Clause 2 passes, which no longer matters.

What widening actually did is more interesting than "no effect": it trades DC accuracy for
consistency. Mean attitude error rises at soft/medium/hard while env-to-env dispersion falls sharply
at hard (`att_norm ss_error_std` -0.8483, roll -0.7828) and pitch overshoot drops to about a third of
baseline at every level. That is the exact mirror of the trade `DESIGN.md` §5 warned about.

**And the heavy tail the probe was aimed at got worse.** Roll `n_gt20` rises in 4 of 4 cells
(0 → 6, 0.33 → 7, 1 → 5.67, 5 → 5.67). Each delta is below the 15-env floor, so none is individually
REAL — but per-cell floors do not aggregate, and a 4-of-4 sign pattern against the mechanism's own
prediction belongs in the record rather than in the noise bucket. The mechanism argued that widening
the band would admit the sustained-offset population into the accumulator and help precisely these
envs; it did the opposite.

Two limitations, both stated rather than buried. Run B ended on **18 expansions / KL 2.1600** against
E-int's **19 / 2.2800** — about 5 % less curriculum, so part of the regression may be curriculum
shortfall rather than the gate. The two matched exactly at 9 and 9 at iteration 2519, so the gap
opened only in the second half and a mid-run check alone would have been falsely reassuring; this
check existed only because Run A had just shown that a 5000-iteration run stops at ~65 % of budget.
Separately, E-int reached 5000 as a resume chain while this is a fresh run — established practice in
this campaign (the Koopman arm and Phase D were both accepted under it) but a real difference.

### Run C — R6 narrow arm (`trpo_gate005_s30_260805_112701`) — NULL, fails both clauses

Confirmed as the narrow arm (0.05) at the Run B mid-run checkpoint per `DESIGN.md` §3. Launched
11:26:55 with a **22-second** GPU0 gap; override verified at 11:30:55. Finished 4999/5000 at 16:21
with zero error-pattern lines; its handoff carried a 12:00 guard that would have skipped the launch
rather than start a run that could not be evaluated in time.

Same protocol: pairing checked before any metric (23/23 at all four levels against both E-int
baselines), survival read before accuracy (100 % except hard 98.44 %, one env of 64 — below the
1.6 pp floor, so nothing is survivorship-contaminated).

**Twenty REAL flags, every one of them worse, zero improvements.** Clause 1 fails — `att_norm`
`ss_error` regresses REAL at all four levels (+0.4572 / +0.2729 / +0.3313 / +0.4402). Clause 2 fails
too, which the widen arm survived: roll `os_env_mean` breaches its 10.0 floor at none/soft/medium
and roll `n_gt20` breaches its 15-env floor at **all four** levels (+42.00, +33.00, +27.33, +16.33).

**The three points together say more than either arm alone.** On roll `n_gt20` — the heavy-tail
metric the mechanism targets — the default wins at every level, reading 0.10 / 0.20 / 0.05 per cell:

| level | roll `n_gt20` (of 64 envs) |
|:--|:--|
| none | **0.00** / 6.00 / 42.00 |
| soft | **0.33** / 7.00 / 33.33 |
| medium | **1.00** / 5.67 / 28.33 |
| hard | **5.00** / 5.67 / 21.33 |

Both directions are worse — mildly when widening, off a cliff when narrowing. The knob is not inert;
it is already at or beside its optimum, which is a more useful answer than a flat null. The
mechanism the lead argued is confirmed with its sign: the gate is a settling-band accumulator, so
narrowing it excludes exactly the sustained-offset envs that need integral action.

**The pre-registration was half wrong in the informative direction.** `DESIGN.md` §5 expected
null-to-small both ways because the policy already gets an ungated 3D bias-EMA buffer (`_bias_ema`,
P-B1). True for widening; false for narrowing — that parallel path does not rescue a too-narrow
gate.

**Single-variable was verified, not assumed.** `agent.yaml` is identical line for line between the
two fresh arms; `env.yaml` differs only in the three gate values once base64 pickle blobs and
run-identity fields are excluded. A decisive negative earns the same scrutiny as a positive.

**An independent instrument had already ranked it last.** Before any eval, Run C's training showed
reward 251.8 against `performance_lb` 250.0 and DORAEMON success 0.5849 against `alpha` 0.5 — the
success bar running through the middle of its return distribution — which throttled its own
curriculum to 17 expansions against 18 (widen) and 19 (E-int), on byte-identical DORAEMON settings.
DORAEMON success is `episode_return >= performance_lb` (`doraemon.py:306`), so the treatment cannot
contaminate that criterion by construction.

**Limits.** One seed per arm, so the ranking is solid but the curve's shape between 0.05 and 0.20 is
not; and E-int is a resume chain against two fresh arms, so only widen-vs-narrow is a clean
same-protocol pair.

### GPU1 — evals

Twelve evals of E-int's checkpoint, all anchored with `--doraemon-dr-from` against E-int's own
learned DR so the four DR levels mean the same thing across runs. Indexed with both decoders in that
run's `eval/README.md`; two are marked VOID with the reason on disk.

The delay sweep measured E-int's response at 20/40/60 ms, paired at `none`:

| | 20 ms | 40 ms | 60 ms |
|:--|:--|:--|:--|
| `att_norm` `ss_error` vs no delay | 2.55× | 6.46× | 12.24× |
| roll `ss_jitter` | 4.84× | 11.54× | 20.55× |

Survival stayed 100 % throughout. Measured bus staleness (0–40 ms attitude) brackets the 20–40 ms
points, where nominal attitude error goes 0.50 → 3.23 deg.

## 4. Corrections made outside the ledger

Closing the leads surfaced four things that were wrong in artifacts other sessions will read.

- **DGX Gate A** carried a saturation checkpoint of ~6750 measured on the retired posttam plant.
  Corrected to **7748**, and the not-saturated-by failure threshold from 9000 to 10000 to keep the
  same margin.
- **DGX Gate B** carried "healthy `success_rate` at saturation is 0.76-0.81", also posttam. On this
  plant healthy is **0.62-0.70** — an operator judging the flagship against the old band would have
  raised a false alarm on a healthy run. The gate now reads the *shape*: declining while the box
  expands is expected; declining after saturation is the failure. Post-saturation `Train/mean_reward`
  likewise moved from 251.4-273.7 to **236.4-265.0**.
- **The Z4 latency sweep's `hard` column** was recorded as a paired comparison and never was.
- **My own reading that the feasibility gate was INERT** was retracted before it reached the wiki: it
  came from a mid-expansion sample (0.84 at iteration 5988), not a steady state (0.666).

Two instrument defects were found and written up, because both will bite again:

- **A Hydra override can be accepted, exit 0, and inject nothing.** `apply_dr_config()` rebuilds the
  randomization config before env creation and again at every DR level, so any field that is not a
  `_DR_TUPLE_FIELDS` dim reverts to its dataclass default. This silently produced an hour of
  byte-identical "delay" evals. When a dedicated CLI flag exists, use the flag.
- **An injection that draws from the RNG unpairs the comparison even when it bites.** Bite and
  pairing are two separate gates and passing the first says nothing about the second.

## 5. What was deliberately not done

- **Stonefish**, entirely — user decision. Three leads died with it rather than waiting.
- **Every hardware measurement** — T200 curve, XW540 step response, IMU convention, TAM CAD
  tolerance, m4 remeasure. User decision. These are DEFERRED-HARDWARE, off the experiment queue, not
  open questions.
- **Applying the two confirmed plant errors.** They are real, and the policy is measurably
  insensitive to both across a two-decade bracket. Applying them would void E-int as the flagship's
  baseline for a change with no measured effect.
- **Multi-seed confirmation** anywhere — standing single-seed screening rule.
- **The latency training half** — see the lead's row above.

## 6. Verification

**Both queries return zero rows, verified 2026-08-05 16:45 KST:**

```
$ omx wiki list --status needs-experiment --root /workspace/constrained-albc
{"pages": [], "corrupt_pages": []}
$ omx wiki list --status needs-apply-before-retrain --root /workspace/constrained-albc
{"pages": [], "corrupt_pages": []}
```

The commands, for re-running:

```
omx wiki list --status needs-experiment --root /workspace/constrained-albc
omx wiki list --status needs-apply-before-retrain --root /workspace/constrained-albc
```

`needs-apply-before-retrain` has returned `{"pages": [], "corrupt_pages": []}` since 06:00.
`needs-experiment` is down to the single R6 row, which Run C closes.

**No lead is hiding in a third state.** A direct frontmatter scan of all 513 pages under
`.omx/registry/findings/` (14:12) reads **73 `resolved`, 1 `needs-experiment`, 439 untagged**, and no
other status value exists in the store — so "both queries return zero" is not a narrow question that
could pass while open work sits under some other label. Twenty-three additional pages contain the
string `needs-experiment` in their *body* (each one records the status it was closed from); only the
R6 page carries it in frontmatter. The scan and `omx wiki list` are independent readers and agree on
that count.
