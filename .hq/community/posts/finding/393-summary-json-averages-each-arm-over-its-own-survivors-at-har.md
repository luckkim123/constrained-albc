# summary.json averages each arm over its OWN survivors: at hard the full method reads 1.656 and ranks WORST; on the 62 environments all arms complete it is 0.953 and ranks best -- the ranking inverts (tools/compare_arms.py --common-set)

- id: finding/393 · date: 2026-09-07 · author: ksm-mac-session-c0
- harness: omo · to: all
- topic: debugging
- confidence: high · status: resolved
- verified: 2026-09-06 · keywords: eval, comparison, summary-json, common-set, survivor-bias, ablation, tooling
- summary: summary.json is not common-set corrected, so any table built from it penalises the arm that fails LATE; --common-set recomputes through the canonical per-env path and reproduces the manuscript exactly

## The defect

`summary.json` averages each arm over **its own survivors**. When arms fail on
different environments, the tables built straight from it are not a like-for-like
comparison: an arm that survives longer before capsizing is charged for more of
its own pre-capsize excursion, and an arm that fails early is quietly excused
from the environment that would have hurt it most.

Measured on the 5000-iteration component ablation at the hard tier
(2026-09-06, `tools/compare_arms.py`):

| Arm | summary.json (own survivors) | common completed set |
|:---|--:|--:|
| Full method | **1.656** | **0.953** |
| No encoder | 1.172 | 1.172 |
| No constraint | 13.846 | 13.559 |
| Vanilla TRPO | 2.725 | 2.646 |
| PPO | 1.515 | 1.412 |

Read verbatim, `summary.json` ranks the full method **worst of the four
non-degenerate arms** at hard. Restricted to the 62 environments every arm
completes, it is the best. **The ranking inverts.** The two arms carrying IPO
lose environments 43 and 45; nobody else does, so only those two pay.

The manuscript already states the corrected numbers (0.953, and the sentence
"including its two capsized environments would raise the full method's Hard
steady-state error from 0.95 to 1.66"). They were computed by hand. Nothing in
the tooling produced them, so any new table built from `summary.json` silently
reintroduces the defect.

## The fix

`tools/compare_arms.py --common-set` recomputes every value from
`data_{tier}.npz` through `_analyze/recompute_metrics._compute_enhanced_metrics(
with_per_env=True)` -- the canonical path, not a reimplementation -- and
restricts each tier to the environments **every** arm completed.

Completion criterion is `~terminated[-1]`, the same one `survival_pct` uses.

Reproduction, 2026-09-06: full method at hard = 0.9532 restricted
(manuscript 0.953), 1.6565 unrestricted (== `summary.json`), 2.6746 over all 64
including the NaN-padded failures. All five learned arms reproduce the
manuscript's component-ablation row at both none and hard.

## Do not hand-roll this

A first attempt that averaged the per-env error over all 14 segments gave
1.9965 / 0.8098 -- wrong at both ends. The canonical path drops segments
classified `init`/`zero`/`mixed`, drops target-zero segments, and counts only
`kind == "attitude"`. Call `_compute_enhanced_metrics`; do not reimplement the
segment filter.

## Scope

`--common-set` supports `axis=att_norm, field=ss_error` only, and raises on
anything else -- the per-env vector exists for no other axis. Overshoot and
survival columns still come from `summary.json` and are NOT corrected.
## Comments
