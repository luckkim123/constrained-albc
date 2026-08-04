---
title: "roll transient is WORST at none DR and improves monotonically as DR hardens (inverted, both runs)"
tags: ["roll", "overshoot", "transient", "dr-scaling", "os_env_mean", "open-lead", "nominal-corner", "doraemon", "id-collision"]
created: 2026-07-21T07:58:14.787774
updated: 2026-08-04T15:58:14.323513
sources: ["diagnose-20260721-164331", "next-20260724-033159", "static_260724_040413", "static_260723_091813", "diagnose-20260728-081953"]
links: ["eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
blocked-on: "Follow-up = nominal-corner exposure (DORAEMON nominal sampling floor), a training-side experiment sequenced 'after C3'. Referent RESOLVED 2026-07-30: C3 = the TEACHER canonical 4-arm x 3-seed ablation set (PLAN.md 216/325/618), DEFERRED to the paper phase by user decision 2026-07-23 -- NOT the student campaign's C3/gruselect arm, which is an unrelated id that shares the label. So this stays blocked on a deferred block. Open question for the human: is 'after C3' a technical dependency or only roster ordering? If ordering, it can be re-prioritised; that is a user decision, not an assumption."
---

# roll transient is WORST at none DR and improves monotonically as DR hardens (inverted, both runs)


[FINDING] Roll transient overshoot is INVERTED against DR level: it is WORST on the nominal
plant and improves monotonically as DR hardens. This holds in both runs compared on
2026-07-21, so it is a property of the policy family, not of any one intervention.

| DR level | A3 roll os_env_mean | anchor roll os_env_mean |
|---|---|---|
| none | 21.486 | 17.022 |
| soft | 17.699 | 15.645 |
| medium | 15.579 | 14.394 |
| hard | 14.730 | 14.172 |

[EVIDENCE: summary.json roll/os_env_mean, all four DR levels, trpo_minstdthr008_260721_064149
eval static_260721_113503 and trpo_biasema_260715_142543 eval static_260716_160156; analysis
diagnose-20260721-164331 §generalization]
[CONFIDENCE: HIGH]

[FINDING] This is counter-intuitive and currently UNEXPLAINED. The naive expectation is that a
harder plant produces a worse transient; the data says the opposite for roll specifically
(pitch os_env_mean is nearly flat across levels, 12.9 -> 10.3 for A3). Any mechanism proposed
must explain why the axis-specific inversion exists on roll and not pitch.
[EVIDENCE: same source, pitch os_env_mean none 12.873 / soft 11.858 / medium 11.114 / hard 10.304]
[CONFIDENCE: HIGH]

[FINDING] Candidate mechanisms NOT yet discriminated (this is the open work, not a conclusion):
(a) eval-protocol artifact — `eval.py static` grades each run on its own learned DR box, so the
`none` level may not be the "easiest" exam in the sense assumed (see
[[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]]);
(b) the policy is trained overwhelmingly on randomized plants and the nominal plant is
effectively an out-of-distribution corner of its own training distribution;
(c) a roll-specific coupling — roll/yaw per-env rho is strongly negative at `none` (-0.562 A3,
-0.947 anchor) and decays to ~0 at `hard`, so whatever couples the two axes is itself
DR-dependent.
[EVIDENCE: analyze.py eval_dr AXIS DECORRELATION blocks, roll_yaw column, all four levels, both
runs; analysis diagnose-20260721-164331 §heavy-tail]
[CONFIDENCE: MED]

STATUS: needs-experiment. No exploration-side lever addresses this — A3 raised sigma and made
the `none` transient WORSE, which is consistent with (b) but does not prove it. The cheapest
next probe is a zero-GPU one: check hypothesis (a) first by reading what DR box `eval.py static`
actually applies at the `none` level for these two checkpoints, before any training run is spent.

---

## Update (2026-07-23T07:42:45.252377)

2026-07-23 curation: status set to needs-experiment -- matches the body's STATUS line and open-lead tag, making this open lead queryable structurally via `omx wiki list --status needs-experiment`.

---

## Update (2026-07-23T19:18:40.914973)

[FINDING] E1/RT-a probe (proposal next-20260724-033159) RESOLVES exam-artifact hypothesis (a):
REJECTED. Re-evaluating the SAME anchor s30 checkpoint (model_4999) under the WIDEST legal exam
(--doraemon-dr-from trpo_biasema_extend8k_260716_162849, terminal DORAEMON = Beta(1,1) on all 20
params = full config box) did NOT lift any randomized level to >= the fixed none. The none-worst
inversion survives the widest exam, so it is NOT an artifact of each run grading itself on its own
lenient learned DR box.

| DR level | own-box roll os_env_mean (pp) | full-box roll os_env_mean (pp) | delta |
|---|---|---|---|
| none   | 13.545 | 13.217 | fixed physics; -0.33 = eval noise |
| soft   | 11.770 | 11.672 | -0.10 |
| medium | 12.201 | 11.355 | -0.85 |
| hard   | 11.872 | 12.979 | +1.11 |

[EVIDENCE: roll os_env_mean per level, own-box eval/static_260723_091813 vs shared-full-box
eval/static_260724_040413 of trpo_buoyanchor_s30_260722_134743, both 64 env cuda:1, code-exec read
2026-07-24]
[CONFIDENCE: HIGH]

[FINDING] Mechanism (b) nominal=OOD-corner is supported in DIRECTION but WEAK in magnitude, so the
lead is PARKED and no training is warranted. none stays the numerically worst level under the full
box, but the margin is only 0.24 pp over full-box hard (which rose +1.11 pp toward none, the only
level that moved materially) and 1.5-1.9 pp over soft/medium. The 0.24 pp none-vs-hard gap is INSIDE
the demonstrated eval noise: none itself moved 0.33 pp (os) and 14->12 (n_gt20) between two
fixed-physics runs, so none and full-box-hard are statistically indistinguishable. Robust none-worst
holds only vs soft/medium (~0.5 deg at 0.30 deg/pp). Below any defensible floor, so the H2-branch
training follow-up (a nominal-sampling DORAEMON floor) is DECLINED on magnitude; do not spend a run.

[EVIDENCE: same two summaries; none-level run-to-run wobble os 13.545->13.217, n_gt20 14->12,
us_env_mean 0.477->0.713, all at fixed nominal physics, so eval is not bit-reproducible (audit 11.2
determinism claim is too strong); pre-registered thresholds H1>=none and clean-H2 margin>=1.0 pp from
proposal next-20260724-033159]
[CONFIDENCE: HIGH]

STATUS: resolved (2026-07-24, E1/RT-a). Probe RAN; hypothesis (a) rejected, (b) real-but-sub-floor.
No training implication. Practical note for all future per-level roll readings: nominal (none) is a
real ~0.5 deg OOD-corner residual vs soft/medium, indistinguishable from full-box hard; treat
sub-1.0 pp per-level os differences as eval noise.

---

## Update (2026-07-24T07:18:34.028573)

[MEASURED 2026-07-24] RT-a shared-exam re-eval DONE (anchor s30, `--doraemon-dr-from trpo_biasema_extend8k_260716_162849` = full config box Beta(1,1) all 20 dims, vs the anchor's own-box). Question: is the none-worst roll inversion an EXAM-LENIENCY artifact (own box too easy at none) or a REAL OOD-corner? Roll os_env_mean under the FULL shared box: none 13.22 / soft 11.67 / medium 11.36 / hard 12.98 pp. none stays the HIGHEST (worst) even when the exam is hardened -> H1 (exam artifact) REJECTED: no randomized level rises to the fixed none value; the inversion does NOT disappear. But not a clean H2 either: none beats soft/medium by >1.5 pp yet beats hard by only 0.24 pp under the full box. VERDICT: H2 (OOD-corner) LEANING / MIXED at the margin -- the roll-worst-at-none pattern is a REAL property of the policy, not exam leniency, but the hard corner closes to within 0.24 pp when the exam is hardened. CONSEQUENCE: lead SURVIVES (not closed) with a real nominal-corner mechanism question; the follow-up (NOT yet proposed) = a DORAEMON floor on nominal sampling, a training-side experiment after C3. Data: experiments/.../trpo_buoyanchor_s30_260722_134743/sweeps/rt_a_extend8k/summary.json.

---

## Update (2026-07-27T23:24:29.885457)

UPDATE 2026-07-28 (HydroRC recenter probe): a discriminating datapoint for the UNEXPLAINED inversion.
Cutting rotational plant damping 10-100x (hydro recenter to Stonefish-measured values, all else
identical to E-int) reproduces the historical roll-overshoot band: roll os_env_mean returns to 17.96 pp
at none (E-int had brought the family from the historical 17-21 pp down to 8.18 pp). The
none-worst/improving-with-DR shape replicates on the recentered plant (17.96/14.43/12.23 none/soft/
medium) with a hard bounce (13.93). Passive plant damping is now the leading candidate for what the
transient tail was missing -- the policy family can hold DC without it but overshoots the step without
it. [EVIDENCE: trpo_hydrorc_s30_260728_013136 eval static_260728_075343 vs trpo_eint_s30_rs2350 eval
static_260727_235736, roll os_env_mean/n_gt20 all levels; report diagnose-20260728-081953]

---

## Update (2026-07-30T05:03:17.174116)

## UNBLOCKED 2026-07-30: the "sequenced after C3" prerequisite is met, and C3 supplied direct evidence for this lead

[FINDING] This lead's blocker was sequencing only -- "follow-up = nominal-corner exposure (DORAEMON nominal sampling floor), a training-side experiment sequenced after C3". C3 ran on 2026-07-29 (trpo_sdeint_c3_gruselect_s30_260729_193732, analysis diagnose-20260729-200134) and the student campaign roster is exhausted, so the prerequisite is met and this is now the front of the training queue.

[EVIDENCE] C3's report independently strengthens the nominal-corner case: C3 has the campaign's WORST dispersion at the none level (att_norm CV 53.5% vs A0g 33.2% and C2 37.0%) and at medium (108.8% vs C2 63.6% and A0g 78.9%), while owning the hard end (CV 132.4% and ss_jitter 0.1877 deg, both better than the teacher's 177.9% / 0.2337). That is the same inverted none-vs-hard shape this page records for the roll transient, now visible on a second metric family (dispersion, not just os_env_mean) and on the campaign's best-tracking arm -- so the nominal corner is where the current best latent tracking still fails to convert.

[CONFIDENCE] MED

Status stays needs-experiment: the follow-up IS a training run (DORAEMON nominal sampling floor), so it is launch-gated like every other arm -- queue via omx queue-launch, never auto-run. What changed is only that nothing sequences ahead of it any more.

One ambiguity to resolve before designing it, carried over from the closeout plan: the original "after C3" note does not say whether it meant teacher-C3 or student-C3. The student C3 is what just ran. If the intended prerequisite was a teacher-side C3, this lead is NOT actually unblocked and the sequencing note needs a correction instead -- check which before proposing the arm.

---

## Update (2026-07-30T05:05:28.338476)

## RETRACTION 2026-07-30 (same day, supersedes the "UNBLOCKED" entry above): "after C3" means the TEACHER canonical C3, which is DEFERRED -- this lead is NOT unblocked

[FINDING] The UNBLOCKED entry written earlier on 2026-07-30 matched the wrong C3. The 2026-07-24 sequencing note refers to the TEACHER canonical C3 -- the 4-arm x 3-seed ablation set -- which user decision 2026-07-23 DEFERRED to the paper phase. The student campaign's C3 arm (gruselect) is an unrelated id in a different campaign's numbering that happens to share the label. The prerequisite is therefore NOT met, and this lead stays blocked on a deferred paper-phase block.

[EVIDENCE] Three independent checks agree, verified 2026-07-30: (1) DATE -- the sequencing note is dated 2026-07-24 and the student campaign student_distill_eint did not exist until 2026-07-29, so its C3 arm could not have been the referent. (2) CONTEXT -- the note sits in the RT-a shared-exam entry whose data is teacher-side (experiments/.../trpo_buoyanchor_s30_260722_134743/sweeps/rt_a_extend8k/summary.json, roll os_env_mean), not student. (3) GRAMMAR -- PLAN.md's canonical-id mapping table (section 3, line 142) lists C3 as a canonical TEACHER id, and PLAN.md:216/325/352/618 define it as "4 ablation arms x 3 seeds, 12 runs, workstation serial, ~60 h, DEFERRED to a later paper phase (user 2026-07-23)". PLAN.md:156 explicitly warns that C1-C3 labels also appear as per-document harness numbering and are excluded from the experiment-id scheme -- the collision is a known hazard in this roster.

[CONFIDENCE] HIGH

Consequence for planning: this lead is NOT the front of the training queue. It is sequenced behind a block the user has deferred, and multi-seed sets are declined outside an explicit paper-phase request, so nothing about it becomes actionable by waiting.

One question the original note leaves genuinely open, and which is the human's to answer rather than mine to assume: whether "after C3" is a TECHNICAL dependency (the nominal-corner arm needs the ablation set's paired-seed baseline to be judged against) or merely ROSTER ORDERING (it was written below C3 in the queue). A 60 h ablation set is an odd technical prerequisite for a single DORAEMON sampling-floor probe, which suggests ordering -- but if it is only ordering, the arm could be re-prioritized ahead of the paper phase, and that is a user decision. Do not treat it as unblocked until that is stated.

What C3-the-student-arm DID contribute here stands on its own and is unaffected by the retraction: C3 has the campaign's WORST none-level dispersion (att_norm CV 53.5% vs A0g 33.2% and C2 37.0%) and worst medium (108.8% vs C2 63.6%) while owning the hard end, which is the same inverted none-vs-hard shape this page records for the roll transient, now visible on a second metric family and on the campaign's best-tracking arm. That is evidence FOR the nominal-corner mechanism; it is not a sequencing unblock.

---

## Update (2026-08-04T15:58:14.323513)

## VERDICT 2026-08-05 -- CLOSED-OUT-OF-SCOPE (backlog-closeout program)

The finding stands and is durable: roll transient is worst at none DR and improves monotonically
as DR hardens, in both runs. Only the proposed follow-up is being closed.

The mechanism is worth recording precisely, because it explains the inversion and it tells a
future reader what a fix would have to do. The none-DR level puts all 21 DR dimensions at their
nominal values SIMULTANEOUSLY. DORAEMON drives each dimension's Beta toward Beta(1,1), i.e.
uniform over its bound. Under a product of 21 near-uniform marginals, the probability that a
single sampled env lands within even +/-10 percent of nominal on every dimension at once is on
the order of 0.2^21, about 2e-15. The nominal corner is therefore not merely under-sampled, it
is effectively never visited: it is a measure-zero region of the training distribution that the
evaluation then tests directly. The policy is worst exactly where it has never trained.

Three reasons the proposed fix (a DORAEMON nominal sampling floor) is not built here.

First, the mechanism does not exist. There is no nominal_floor_prob anywhere in either repo;
ParamSpec.nominal is read exactly once, at BetaDistribution.__init__, to set the initial mean.
Building it means a new config field plus forced-nominal sampling inside
DoraemonScheduler.sample().

Second, and decisively, that change breaks the importance-sampling contract the curriculum
controller runs on. Forced-nominal envs are not draws from the Beta, so either their weights are
wrong or they must be excluded from the IS buffer. Neither variant can be validated inside this
program's clock, and a subtly-wrong curriculum would make the run that tested it uninterpretable
-- a bad result could not be attributed between the mechanism and its implementation.

Third, this page's own 2026-07-30 retraction states the lead is NOT unblocked: its 'after C3'
prerequisite is the TEACHER canonical 4-arm x 3-seed ablation, which the user deferred to the
paper phase on 2026-07-23 (it is not the student campaign's C3, an unrelated id sharing the
label). Building a risky shared-engine change in order to run an item its own page marks parked
is the wrong trade against a hard deadline.

Reopen when the teacher C3 block is undeferred, and treat the IS-weight question as the first
design task rather than an implementation detail.

Recorded by the backlog-closeout program (.omx/programs/backlog-closeout/PLAN.md section 3).
Status flipped to resolved; no experiment is scheduled for this lead.

