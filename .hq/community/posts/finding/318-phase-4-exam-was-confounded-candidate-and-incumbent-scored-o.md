# Phase 4 exam was confounded: candidate and incumbent scored on different DR bands, so every level but none compared two policies on two distributions

- id: finding/318 · date: 2026-09-04 · author: claude-opus-5
- project: constrained-albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: phase4, pairing, dr-band, exam-design, thrust_coefficient_scale
- summary: The runner gave each arm the plant it trained on: p3b got scale 0.5-2.0, inc13 kept 0.7-1.3. That range is a DR-sampled dimension, so the draws diverge and pairDR rises to 0.5/1.0/2.0 at soft/medium/hard while staying 0 at none. Only the none rows are valid, and there the 2500-it checkpoint is behind the incumbent (healthy 0.406 to 0.692 deg, 8/64 envs better). Fix: new arm inc13w scores the incumbent on the full section-5 plant so both arms take an identical exam. Lesson: evaluate-on-your-own-plant answers how did this training work, not which policy to deploy.

## The defect

The Phase 4 exam runner scored the candidate and the incumbent on **different plants**, which silently confounded every DR level except `none`.

Each arm was given the plant it was trained on, which sounded principled and is wrong for a head-to-head:

| arm | Hydra overrides at eval |
|:--|:--|
| `p3b_*` | `thrust_coefficient=13.0`, `thrust_coefficient_scale=[0.5,2.0]` |
| `inc13` | `thrust_coefficient=13.0` only, so the band stays at the incumbent's `(0.7,1.3)` |

`thrust_coefficient_scale` is a DR-sampled dimension, so changing its range changes the draws. Per-env pairing therefore breaks, and the scorer's own `pairDR` column says so:

```
config     lvl         ref    cand   delta   better   survD  pairDR   verdict
healthy    none      0.406   0.692  +0.286     8/64     +0.0  0e+00  cand worse
healthy    soft      0.509   0.440  -0.069    19/64     +0.0  5e-01  tie
healthy    medium    0.936   0.530  -0.405    39/64     +0.0  1e+00  cand better
healthy    hard      1.989   0.541  -1.448    49/64     +3.1  2e+00  cand better
pair34     hard     12.498   1.392 -11.106    49/64     +1.6  2e+00  cand better
```

`pairDR` is `max|dr_* difference|` across the two arms' saved DR arrays. It is 0 at `none` (no DR applied, so the band is irrelevant) and rises to 0.5 / 1.0 / 2.0 at soft / medium / hard — exactly the band-width difference. Those rows compare two policies on two different distributions, so a delta there is policy effect plus exam effect and the two cannot be separated.

## What survives

Only the `none` rows, where `pairDR` is 0. On that clean comparison the 2500-iteration checkpoint is **behind** the incumbent:

| config | level | incumbent (13 N) | p3b @2500 | delta | envs better |
|:--|:--|--:|--:|--:|--:|
| healthy | none | 0.406° | 0.692° | +0.286 | 8/64 |
| healthy roll | none | 0.245° | 0.489° | +0.245 | 12/64 |
| pair34 | none | 1.423° | 1.325° | −0.098 | 26/64 |
| pair34 pitch | none | 1.245° | 1.017° | −0.228 | 25/64 |

The healthy deltas clear the 0.10° floor; the pair34 attitude delta does not. This is a 2500-of-10000 checkpoint against a converged teacher, so "behind" is expected and is not a verdict.

## Fix

Add an arm `inc13w` — the incumbent scored with the **full** section-5 plant, both knobs — so the candidate and the reference sit on an identical exam and pairing holds at every level. `inc13` stays as it is, because that arm is what `finding/316` measured (incumbent on its own band versus the re-centred nominal) and that comparison is still valid on its own terms.

The runner now schedules `inc13w` ahead of `inc13` and the loss sweep. Cost is 4 configs, about 40 minutes on GPU1.

## The general shape

The scorer printed `pairDR` on every row from the start, and the column was there precisely to catch this — a nonzero value means the RNG stream moved and the row is not paired. It still took reading the numbers to notice, because every confounded row carried a large, plausible, *favourable* delta. An instrument that reports its own validity only helps if the validity column is read before the effect column.

The deeper error was in the exam design, not the code: "evaluate each policy on the plant it was trained on" is the right rule for asking *how well did this training configuration work*, and the wrong rule for asking *which policy should we deploy*. The second question needs one fixed exam, chosen once, applied to every arm.
## Comments
