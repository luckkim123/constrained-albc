# albc

The prose half of the board. `runtime/board.json` is what hooks read; this is what
people read. No campaign is active — experiment campaigns are tracked by
`omx campaign-status`, and multi-stage lines by `programs/<id>/PLAN.md`.

## Goal

Train and verify a constrained 6-DOF UUV attitude controller (ConstraintTRPO + IPO +
encoder) to a state that survives deployment, and keep every run's evidence traceable
from its `run_id` back to the code that produced it.

## Decisions

| # | Date | Decision | Because | Reversal cost | By |
|:--|:-----|:---------|:--------|:--------------|:---|
| D1 | 2026-09-01 | Migrate the `.omx` store into this repo's own `.hq` anchor, converting 300 wiki pages into posts | store-spec §2: one anchor per git repository, harness recorded as a field rather than a directory | Low — the legacy store is preserved under `~/.claude/hq-purged/` and in git history | session |
| D2 | 2026-09-01 | Backfill `harness: omx` onto all 300 converted posts | `convert-wiki-form.py` dropped the field, so `hq query --harness omx` returned nothing on a store built entirely by omx | None — a frontmatter line | session |
| D3 | 2026-09-01 | Seed the omo payload (`rules/`, `HUB.md`) | The store existed but no vendor worker would have seen this project's evaluation and analysis discipline | Low — delete the files | session |
| D4 | 2026-09-01 | Keep `programs/koopman-lifting/step3_modules/*.pt` in the tracked `community/` layer | store-spec §3 rule 4 would put a regenerable artifact in `work/`, but the refit input (`experiments/.../static_260805_192608/data_*.npz`) is itself gitignored — demoting the weights would lose both the artifact and the means to rebuild it | None — move them to `work/experiments/` if the input ever becomes tracked | session |

Append only. Numbers are monotonic and never reused.

## Artifact map

| What | Where |
|:---|:---|
| Posts (experiment knowledge) | `posts/<category>/<NNN-slug>.md` |
| Multi-stage experiment plans | `programs/<id>/PLAN.md` |
| Shared rules (vendor payload) | `rules/` |
| omx profile (metrics, adapters, tree) | `../config/experiments/profile/` |
| Campaign and run ledgers | `../work/experiments/{campaigns,runs}/` |
| Per-run results (SSOT) | `experiments/rsl_rl/<exp>/<group>/<run_id>/analysis/*/report.md` |
| Heavy run data (checkpoints, TB) | `logs/rsl_rl/...` |

## Reversals

- The `<group>` / wandb-project split was reversed on 2026-07-14: the group folder name,
  the wandb project name, and the experiment purpose are now one string. The earlier
  split produced a 17-project scatter.
- `docs/results/` is no longer a result location; the `experiments/` tree is the SSOT.
