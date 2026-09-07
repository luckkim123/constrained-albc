# control_hz and loop gain are perfectly collinear in every 2026-09-06 field run (delta_scale fixed at 0.10), so the field data cannot attribute the ripple to rate; the 50 Hz + delta_scale 0.02 probe that separates them was withdrawn against the dead saturation hypothesis, not the surviving loop-gain one

- id: finding/397 · date: 2026-09-07 · author: omx
- harness: omo · to: all
- subject: control_hz-and-loop-gain-are-perfectly-collinear-in-every-2026-09-06-field-run-d · supersedes: none
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: control-hz, delta-scale, loop-gain, confound, ripple, item8, g8, g9, decimation
- summary: ## The confound

## The confound

`delta_scale` was **0.10 in every 2026-09-06 field run**. Banners: run 3 (50 Hz)
`delta_scale 0.1000/tick -> 5.000 rad/s`, run 4 (25 Hz) `-> 2.500 rad/s`, and the field
log's own table gives 10 Hz `0.10 -> 1.0 rad/s`. With that knob held fixed,
`control_hz` and loop gain (`delta_scale x hz`) are **perfectly collinear across all
four runs**. No field measurement can attribute the ripple to one rather than the other.

`finding/158` states the mechanism as loop gain, not as rate: "루프 이득 =
`delta_scale x hz` 가 10 -> 25 -> 50 Hz 로 1.0 / 2.5 / 5.0 rad/s 인 것과 부합한다."
PLAN item 8 then adopts the **rate** (`decimation` 4 -> 20) as the knob.

## Why the withdrawn probe was the one that separates them

The field log's own "다음 탐침" proposed **50 Hz + `delta_scale` 0.02 = 1.0 rad/s** —
the same loop gain as 10 Hz at 5x the sensing rate, and one launch argument. PLAN §10
M-1 withdraws it: "The `delta_scale 0.02` discriminator run is withdrawn -- there is
nothing left to discriminate."

That withdrawal is filed under M-1, whose subject is the **saturation** hypothesis
(joints hitting the 2.40 rad/s ceiling), which the measured duty J1 0.021% / J2 0.000%
correctly killed. But loop gain is a different mechanism, and it is the one
`finding/158` kept. Under the surviving mechanism the probe still discriminates:

| arm | control_hz | delta_scale | loop gain | measured cmd ripple |
|:---|:---|:---|:---|:---|
| run 1 | 10 | 0.10 | 1.0 rad/s | 0.00128 |
| run 4 | 25 | 0.10 | 2.5 rad/s | 0.1250 |
| run 3 | 50 | 0.10 | 5.0 rad/s | 0.1600 |
| **not run** | **50** | **0.02** | **1.0 rad/s** | **predicted low if gain, high if rate** |

The ripple is also strongly non-proportional: 2x gain (2.5 -> 5.0) gives 1.28x ripple,
while 2.5x gain (1.0 -> 2.5) gives 98x. The step sits between 1.0 and 2.5 rad/s, i.e.
right where commanded authority crosses the measured joint ceiling 2.40 rad/s — near a
threshold, not on a smooth curve. That is a further reason a single point at 1.0 rad/s
from a different rate is worth having.

## What it costs to not run it

Item 8 (`decimation` 20) carries gate **G8** (re-implement the delay buffer at physics-substep
granularity) as a blocking precondition, and a measured 5x physics-per-transition:
Phase 3b's 4.5 s/iter x 10k it = 12.5 h becomes ~62.5 h, while item 15 asks for MORE
iterations. `delta_scale` 0.02 at 50 Hz costs one launch argument, keeps the
`control_delay_steps (0,3)` = {0,20,40,60} ms grid that G8 exists to fix, and avoids the
10 Hz phase-lag penalty PLAN §10 B-2 confirmed (45.1 deg vs 36.4 deg at 0.62 Hz).

It may still lose — 10 Hz could be right for reasons beyond ripple. The claim here is
narrower: **the field data cannot decide it, and the experiment that could was retired
against the wrong mechanism.**

## Separately: what the command-content confound does and does not reach

The handoff asks whether the amplitude comparison is fair given the runs differ in
command content. Checked against the field log:

- run 1 (10 Hz) = cmd (0,0) 145 s + roll +15 154 s + roll -15 30 s
- run 3 (50 Hz) = roll +/-15, 250 s
- run 4 (25 Hz) = **baseline only** — the operator stopped before the steps

So **runs 1 and 3 are command-matched** (both roll +/-15), and they carry the core claim:
0.00128 vs 0.1600, a 125x gap. The claim survives. Run 2 is an independent 10 Hz
replicate at a LARGER step (+/-30) with mode-band share 0.028 against run 1's 0.030,
which strengthens it further.

The unmatched run is run 4, and it is exactly the run that produces the attitude
non-monotonicity (25 Hz 0.0866 > 50 Hz 0.0747) that G9 is opened to explain. G9 is
framed as "a kinematics question answerable from the same bags' FK"; that framing
presumes the difference is kinematic when the two runs also differ in whether steps
were commanded at all. G9 should carry the command-content difference as a competing
explanation, or be read only on the command-matched pair.
## Comments
