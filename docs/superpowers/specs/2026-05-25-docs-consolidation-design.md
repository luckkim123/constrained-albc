# Docs Consolidation Design

**Date:** 2026-05-25
**Goal:** Move project documentation out of the pristine `isaaclab` fork
(`isaaclab/docs/hero/`, 43 files, ~700 KB) into `constrained-albc/docs/`,
reorganized in Diátaxis style, with stale material deleted and historical
material compressed into lookup-friendly consolidated files.

## Motivation

- `isaaclab/docs/hero/` violates the `isaaclab-pristine` rule (zero of our code/docs
  in the upstream fork). Removing it restores the fork to clean state.
- The `hero/` naming is stale (project moved off `hero_agent` to `Isaac-FullDOF-TRPO-v0`).
- Content is a mix of current design docs, deprecated-approach docs, and historical
  experiment/changelog records that should be archived, not navigated.

## Source Classification (43 files)

### DELETE — stale, misleading if followed (3)
- `architecture/training_pipeline.md` — HORA/RMA 2-phase pipeline (deprecated)
- `archive/rl_tdc_comparison.md` — abandoned RL-TDC path
- `archive/sac_mpc_monitoring.md` — abandoned SAC-MPC experiment

### KEEP — current living docs (12), de-staled where MIXED
- `deployment_guide.md`
- `architecture/`: tdc_control_law, tdc_literature_survey, dynamics_analysis,
  reward_functions, theoretical_analysis
- `environment/`: domain_randomization, sim_to_real
- MIXED (strip deprecated variant mentions + "BEST POLICY" claim):
  system_overview, physics_environment, README
- `experiments/dr_training_survey.md` (literature reference)

### COMPRESS — historical record → consolidated lookup files (28), raw deleted
- 9 experiment rounds + encoder_ablation + arm_freeze_analysis → `experiments-archive.md`
- 8 plans/ design docs → `design-history.md`
- 4 history/ logs → `debug-history.md`
- 4 changelog_*.md → folded into `experiments-archive.md` summary + the JSON
- `experiments_index.json` → kept as-is (`experiments-index.json`, key-value lookup)

## Target Structure (Diátaxis)

```
constrained-albc/docs/
├── README.md                 # doc index / navigation (replaces hero/README)
├── installation.md           # existing, kept
├── architecture.md           # existing, kept (package layout + RSL-RL fork)
├── explanation/              # understanding-oriented (theory / "why")
│   ├── system-overview.md    ├── dynamics.md         ├── reward-design.md
│   ├── tdc-control-law.md    ├── tdc-literature.md   ├── constraint-theory.md
│   └── dr-strategies-survey.md
├── how-to/                   # task-oriented
│   ├── deploy.md  ├── domain-randomization.md  ├── sim-to-real.md  └── physics-tuning.md
└── reference/                # lookup / archive
    ├── experiments-index.json   # machine-readable key-value (settled_decisions + runs)
    ├── experiments-archive.md   # per-round summary table (what changed → result → verdict)
    ├── design-history.md        # plans/ timeline table
    └── debug-history.md         # merged bug/tuning logs
```

`tutorials/` (4th Diátaxis quadrant) intentionally omitted — research repo; README
quickstart + how-to/deploy cover onboarding. No empty stubs.

## Decisions (from user)

- **obs-dim conflict** (JSON 87D/24D vs memory 81D/23D): verified against code
  (`albc_env.py:861`, `mdp/observations.py`). Code = **87D obs / 24D privileged**.
  All docs unified to 87D/24D. (Stale memory entry updated separately.)
- **raw historical files**: summarize only, delete raw. Consolidated per-category
  files made lookup-friendly (what was changed, what the result was). JSON index
  retained for key-value lookup.
- **commit**: reorganize only; no git commit in this task.

## Non-goals

- No edits to isaaclab code or upstream RST docs (only delete `docs/hero/`).
- No content rewrites of CURRENT docs beyond de-staling MIXED ones and unifying obs dim.
- No new tutorials.
