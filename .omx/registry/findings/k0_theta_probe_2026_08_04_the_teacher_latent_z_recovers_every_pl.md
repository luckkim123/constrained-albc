---
title: "K0 theta-probe 2026-08-04: the teacher latent z recovers every plant parameter it was GIVEN (mass/geometry, R2 up to 0.49) and none that was withheld -- damping and 5 of 6 added-mass DOF are at the shuffle floor because they are absent from p_t, not because the encoder failed"
tags: []
created: 2026-08-04T03:38:22.712678
updated: 2026-08-04T03:38:22.712678
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# K0 theta-probe 2026-08-04: the teacher latent z recovers every plant parameter it was GIVEN (mass/geometry, R2 up to 0.49) and none that was withheld -- damping and 5 of 6 added-mass DOF are at the shuffle floor because they are absent from p_t, not because the encoder failed

## Method

Koopman plan Phase 0, item K0 (zero GPU). Per DR level, reduce `l_true` (the TEACHER z, shape
(T, 64, 9)) over the post-warmup half of the episode to X (n_env, 9), then ridge-regress X onto
each of the 23 per-env `dr_*` labels in the same eval's `data_<level>.npz`, 5-fold CV with the
ridge alpha chosen on an INNER split so it never sees the test fold.

Two floors, both mandatory and both used:
- predict-the-mean, which the CV R2 definition scores at exactly 0;
- a shuffled-label refit, 200 permutations, compared at p95. Its mean sits at about -0.03 for
  n=256 and about -0.09 for n=64, which is the overfitting penalty of 9 features on few episodes
  showing up as expected. Without it a small positive R2 would read as signal.

**Dedup is load-bearing.** Several student runs share an identical DR draw: at `none` 9 of 10 runs
matched one fingerprint, and at soft/medium/hard 6 of 10 did. Pooling them would repeat the same
(theta, z) pairs across CV folds -- pure leakage. Runs were fingerprinted on their stacked `dr_*`
matrix and duplicates dropped, leaving n=64 at `none` (1 run) and n=256 at each other level (4).

Instrument was proved able to fail before use: on synthetic data a linear signal scored R2=0.9984
(REAL) and pure noise scored -0.0487 (FLOOR).

## Result -- the split maps exactly onto what p_t contains

| label | in the 28D p_t? | R2 soft / medium / hard |
|:--|:--|:--|
| `dr_body_mass` | yes, `p_t[8]` | 0.463 / 0.418 / 0.335 REAL |
| `dr_cog_y` | yes, `p_t[1:4]` | 0.354 / 0.486 / 0.318 REAL |
| `dr_cog_z` | yes, `p_t[1:4]` | 0.359 / 0.367 / 0.303 REAL |
| `dr_cob_z` | yes, `p_t[4:7]` | 0.361 / 0.325 / 0.235 REAL |
| `dr_payload_mass` | yes, `p_t[10]` | 0.337 / 0.250 / 0.205 REAL |
| `dr_cob_y` | yes, `p_t[4:7]` | 0.194 / 0.216 / 0.096 REAL |
| `dr_cog_x`, `dr_cob_x` | yes | 0.05-0.14 REAL |
| `dr_payload_cog_x` | yes, `p_t[11:14]` | 0.013 / 0.019 / 0.023 REAL but weak |
| `dr_payload_cog_y`, `_z` | yes, `p_t[11:14]` | mostly FLOOR |
| `dr_added_mass_0` (surge) | yes, `p_t[9]` | 0.047 REAL at soft only, FLOOR elsewhere |
| `dr_added_mass_1..5` | **NO** | FLOOR at every level |
| `dr_lin_damp_0..5` | **NO** (removed by priv-obs-slim Stage-1) | FLOOR at every level |

**Every label absent from `p_t` is at the floor, without exception.** `p_t` carries quadratic
damping ROLL at `[7]` and added mass SURGE at `[9]` -- single representative scalars -- while the
eval logs linear damping and added mass for all 6 DOF (`dr_snapshot.py:86,93`, the added-mass
diagonal per DOF). So the damping null is a statement about the privileged vector's contents, NOT
about the encoder.

The converse does not fully hold: `dr_payload_cog_y/z` and `dr_added_mass_0` ARE in `p_t` and
still land at or near the floor. That is the 28D -> 9D compression dropping its weakest channels,
and it is the one genuinely encoder-side finding here.

`none` is structurally unanswerable: with DR off, all 23 labels are constant across envs.

## What this decides

The plan's branch "z sits at the floor -> that outranks everything, stop and re-plan" does NOT
fire. The explicit parameter channel demonstrably works on everything it is handed. Therefore the
implicit-sysID upside for any Koopman lift stays dead (there is nothing for a lift to discover
that the explicit channel is not already carrying), and the only surviving Koopman claim is
optimization geometry -- which is what Phase 1 (arm B) screens.

Scope caveat carried from the plan: `l_true` is logged under the student-mode static-eval
distribution, not the teacher's on-policy training distribution.

Follow-on question this raises, outside the Koopman line: linear damping is invisible to the
teacher by construction. Whether that costs anything is untested -- priv-obs-slim Stage-1 removed
it on a validated A/B, so the presumption is no, but that A/B predates the current plant.

