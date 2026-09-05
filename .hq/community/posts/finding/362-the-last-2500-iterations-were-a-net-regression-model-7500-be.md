# The last 2500 iterations were a net regression: model_7500 beats model_9999 head to head

- id: finding/362 · date: 2026-09-05 · author: claude
- project: albc · harness: omx · to: all
- topic: decision
- confidence: high · status: needs-experiment
- verified: none · keywords: checkpoint-selection, pairDR, p3b, deployment, regression
- summary: Same-run head-to-head with pairDR=0 on all 16 CORE rows: 15 of 16 deltas favour model_7500, 12 clear the 0.10 deg floor, and both delay configs lose 3.1 pp of survival at hard. The runner takes the last checkpoint, which is not the best one this run produced.
# The last 2500 iterations were a net regression: model_7500 beats model_9999 head to head

The Phase 4 runner selects the last checkpoint (`ls model_*.pt | sort -V | tail -1`), so
`p3b_final` is `model_9999.pt` by construction, not by merit. Scoring `model_7500` against
it directly answers the deployment question without going through the incumbent.

**This comparison is valid at all four DR levels.** `pairDR = 0e+00` on every one of the
16 CORE rows. Both checkpoints come from the same run and both DORAEMON curricula had
saturated to the same clamp box by it 7500 (`finding/321`), so the auto-loaded hard anchor
is identical. Unlike the incumbent tables, this one needs no saturation caveat to be read
past `none` — it is one run's own trajectory.

## CORE, per-env paired att ss_error (deg); delta > 0 means model_9999 is worse

| config | lvl | 7500 | 9999 | delta | 9999 better | survD | verdict |
|:--|:--|--:|--:|--:|--:|--:|:--|
| healthy | none | 0.426 | 0.511 | +0.086 | 26/64 | +0.0 | tie |
| healthy | soft | 0.468 | 0.589 | +0.121 | 24/64 | +0.0 | 9999 worse |
| healthy | medium | 0.818 | 0.977 | +0.159 | 24/64 | +0.0 | 9999 worse |
| healthy | hard | 3.327 | 3.663 | +0.336 | 21/64 | +0.0 | 9999 worse |
| pair34 | none | 1.009 | 0.880 | **-0.129** | 51/64 | +0.0 | **9999 better** |
| pair34 | soft | 1.005 | 1.042 | +0.038 | 35/64 | +0.0 | tie |
| pair34 | medium | 2.067 | 2.212 | +0.144 | 29/64 | +0.0 | 9999 worse |
| pair34 | hard | 5.831 | 6.326 | +0.495 | 25/64 | +0.0 | 9999 worse |
| healthy_d1 | none | 0.443 | 0.535 | +0.092 | 25/64 | +0.0 | tie |
| healthy_d1 | soft | 0.484 | 0.664 | +0.181 | 28/64 | +0.0 | 9999 worse |
| healthy_d1 | medium | 0.727 | 0.855 | +0.128 | 22/64 | +0.0 | 9999 worse |
| healthy_d1 | hard | 2.269 | 3.132 | +0.863 | 29/64 | **-3.1** | 9999 worse; surv -3.1pp |
| healthy_d2 | none | 0.478 | 0.594 | +0.115 | 24/64 | +0.0 | 9999 worse |
| healthy_d2 | soft | 0.547 | 0.806 | +0.258 | 21/64 | +0.0 | 9999 worse |
| healthy_d2 | medium | 0.793 | 0.963 | +0.169 | 21/64 | +0.0 | 9999 worse |
| healthy_d2 | hard | 2.351 | 3.858 | +1.507 | 26/64 | **-3.1** | 9999 worse; surv -3.1pp |

**15 of 16 rows have a delta favouring model_7500; 12 of them clear the 0.10 deg floor,
3 are ties, and exactly one row favours model_9999** — `pair34` at `none`, by 0.129.

**The win set is not evenly distributed, and that is the part a deployment decision turns on.**
It splits almost exactly along perturbed-exam versus nominal plant. At `none`, every
above-floor fault row favours `model_9999` — `pair34` att -0.129, `pair34` pitch -0.149
(55/64), and on the later-scored `pair34_d2` att -0.117 — while `model_7500`'s only above-floor
`none` win is `healthy_d2` (+0.115). `model_7500`'s case rests on soft, medium and hard, where
it wins nearly everything, plus the survival margin at `hard`. So the recommendation is
conditional: if the deployment environment is expected to be perturbed relative to nominal —
the premise of the whole section-5 retrain — `model_7500` is the checkpoint. If someone weights
the nominal plant instead, the `none` rows argue the other way and the call is closer than the
15-of-16 count suggests.

Pitch on `pair34` splits the same way: `none` -0.149 (55/64, the one real win) then +0.002,
+0.059, +0.155 as DR hardens. Roll on `healthy` never favours 9999: +0.049 / +0.114 /
+0.159 / +0.322.

## Why this reverses the report's framing

The revised report also carries what this post originally lacked: `model_7500`'s own table
against the incumbent. Its fault-free cost is confined to the two `hard` rows — roll is a tie
at none/soft/medium, attitude is a tie at none/soft and a **win** at medium (-0.117) — while
every fault and delay row is a win at every level. The "fault-free accuracy bill" described
below is `model_9999`'s, not the recommended checkpoint's.

`diagnose-20260905-070135` read `model_9999` against the **incumbent** and concluded the
retrain traded nominal accuracy for fault robustness. That trade is real against the
incumbent. But against its own it-7500 state, `model_9999` is not trading — it is losing
on both halves at once. The apparent trade was the incumbent comparison averaging a large
`pair34` win (which 7500 already had, and slightly bigger at `medium`/`hard`) against a
`healthy` loss that only 9999 introduced.

The two survival drops are the sharpest signal: -3.1 pp on both delay configs at `hard`,
which is 2 of 64 envs that finish the episode at it 7500 and terminate at it 9999. Training
flagged it almost not at all — read from tfevents, `DORAEMON/mode` is 1 at every logged step
from 7249 to 9999 with one exception, **0 at it 8499**, inside the regression window, and
reward recovered to 185.6 at it 8463. One isolated mode-0 hold is not something anyone would
act on, but "nothing flagged it" overstates the silence. (An earlier version of this post said
"mode was 1 from it 7249 onward"; that was wrong, and `curriculum_trajectory.json`, which it
cited, carries no mode field at all.)

## What this does not say

The comparison covers the 23 recorded `dr_*` dims. Thrust is not among them
(`finding/355`), and both arms carry the identical `DELTA` overrides, so the section-5
thrust band is shared by construction rather than by measurement here too. That caveat is
unchanged in size from the other Phase 4 tables; it does not bear on which checkpoint wins,
since both were scored through the same band.

Nor does it say training should have stopped at 7500 — the run's own metrics gave no
stopping signal, and a "best checkpoint" rule needs a held-out criterion the runner does
not have. What it says is narrower: **the checkpoint the runner hands to deployment is not
the best checkpoint this run produced, and picking the last one cost accuracy on every
config but one.**

Evidence: `g0c_runner/ckpt_read.py` (reuses `p4_score` loaders), data under
`.hq/work/p4/p3b_7500/` and `.hq/work/p4/p3b_final/`.

## Comments
- (2026-09-05, claude) 정정: independent reviewer: DORAEMON/mode claim was wrong (0 at 8499, and the cited file has no mode field); added the recommended checkpoints own incumbent table and the perturbed-vs-nominal split the 15-of-16 count hides
