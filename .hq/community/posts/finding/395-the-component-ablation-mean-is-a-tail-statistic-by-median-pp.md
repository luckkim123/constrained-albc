# The component ablation mean is a TAIL statistic: by median PPO beats the full method at hard (0.658 vs 0.685) and no-encoder beats it at soft; every median gap among those three is 3-5x SMALLER than the measured between-seed spread. What survives is tail control (max 4.46 vs 15.78 deg)

- id: finding/395 · date: 2026-09-07 · author: ksm-mac-session-c0
- harness: omo · to: all
- topic: debugging
- confidence: high · status: needs-experiment
- verified: 2026-09-06 · keywords: ablation, mean, median, tail, ppo, encoder, seed-noise, paper, eval
- summary: Recomputed at mean/median/P90 on the common completed set: the full methods advantage over PPO and no-encoder exists only in the tail at hard, and the typical-case gaps are inside seed noise. Against vanilla TRPO, TDC, no-constraint and PID it wins 55-62 of 62 environments.

## What the mean-only table hides

The component ablation reports one number per cell: the mean `att_norm` steady-state
error over environments. Recomputed on the common completed set at every tier
(`tools/compare_arms.py --common-set --stat {mean,median,p90}`, 2026-09-06):

| Arm | none | soft | medium | hard |
|:---|--:|--:|--:|--:|
| **mean** — Full method | 0.605 | 0.552 | 0.598 | **0.953** |
| **mean** — No encoder | 0.569 | 0.508 | 0.600 | 1.172 |
| **mean** — PPO | 0.577 | 0.516 | 0.562 | 1.412 |
| **median** — Full method | **0.537** | 0.514 | 0.513 | 0.685 |
| **median** — No encoder | 0.562 | **0.465** | **0.506** | 0.708 |
| **median** — PPO | 0.576 | 0.492 | 0.544 | **0.658** |
| **P90** — Full method | 0.880 | 0.723 | 0.818 | **2.002** |
| **P90** — No encoder | **0.625** | 0.680 | 0.874 | 2.613 |
| **P90** — PPO | 0.758 | **0.604** | **0.728** | 2.169 |

By **median**, the full method is best at exactly one of four tiers (none) and is
the *worst* of these three at soft. By **P90** it is best at exactly one tier
(hard) and worst at none. Only the mean puts it first at hard.

## Where the mean comes from

Per-environment maxima over the 62 common environments, hard tier:

| Arm | mean | median | P90 | max | worst env |
|:---|--:|--:|--:|--:|--:|
| Full method | 0.953 | 0.685 | 2.002 | **4.461** | 32 |
| No encoder | 1.172 | 0.708 | 2.613 | 7.421 | 11 |
| PPO | 1.412 | 0.658 | 2.169 | **15.776** | 11 |

PPO's mean is 1.5x the full method's while its median is *lower*. The gap is one
environment. Paired per-environment counts against the full method at hard
(`full better / comparable envs`, median ratio):

    no_encoder     31 / 62    1.03x
    ppo            28 / 62    0.94x
    no_both        55 / 62    2.26x
    tdc            55 / 62    3.27x
    no_constraint  62 / 62   17.64x
    pid            62 / 62   26.44x

Against PPO and no-encoder the full method is a coin flip per environment. Against
vanilla TRPO, TDC, no-constraint and PID it wins nearly everywhere.

## The honest reading

The between-seed spread measured in the teacher-selection section is **0.132-0.171
deg** at these tiers. Every median gap among {full, no-encoder, PPO} is 0.03-0.05
deg -- **three to five times smaller than seed noise**, at single seed. Those three
arms are not separated in typical-case accuracy by this data.

What IS outside seed noise is the tail: 4.46 vs 15.78 deg worst environment, and
the 62/62 sweeps against the unconstrained arms. So the defensible claim from this
ablation is **tail control under hard DR**, not typical accuracy -- which is what a
safety constraint is supposed to buy. The current mean-only presentation states a
weaker thing in a way that invites the stronger reading.

## Caveats that bound this

- Single seed per arm, 5000-iteration budget. The deployed teacher (model_9998) is
  not in this comparison.
- Every arm here was graded on the `DomainRandomizationCfg` class default, not the
  section-5 plant (finding/391). The tail behaviour may move on the new anchor
  decision/392 adopts.
- Common completed set only (62/64 at hard; envs 43, 45 excluded) -- see finding/393.

## Tooling

`--stat {mean,median,p90}` on `--common-set`; `--paired <baseline> --paired-level
<tier>` draws the per-environment scatter (log-log, parity diagonal, dropped
environments named in the title and manifest).
## Comments
