---
title: "engine-gap: omx report path assumes flat run_id, breaks nested experiments/rsl_rl/<exp>/<run_id> tree"
tags: ["engine-gap", "omx", "paths", "run-id-tree", "output-root"]
created: 2026-06-02T10:28:14.180482
updated: 2026-06-02T10:28:14.180482
sources: ["20260602-192051-diagnose"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: omx report path assumes flat run_id, breaks nested experiments/rsl_rl/<exp>/<run_id> tree

[ENGINE-GAP] omx writes analysis output to a FLAT run_id tree (output_root/<run_id>/analysis/<id>/), but this workspace's canonical run_id tree is NESTED: experiments/rsl_rl/<exp>/<run_id>/ (rule 03-analysis-quality; the run dir has the train->logs symlink + config/ + eval/ siblings). On analysis 20260602-192051-diagnose the report.md landed at experiments/260525_232805_trpo_main_teacher/analysis/... (orphan, missing the rsl_rl/albc_trpo_teacher/ middle segment) instead of experiments/rsl_rl/albc_trpo_teacher/260525_232805_trpo_main_teacher/analysis/... where eval/ already lives. Had to mv->verify->rm by hand to fix.

[WHERE] omx-core/omx_core/omx_paths.py:265 OmxPaths.analysis_dir() = self._out_root(output_root) / run_id / 'analysis' / analysis_id. The run_id is appended directly under output_root with no support for a nested experiment-group middle path. report_md()/manifest_json()/analysis_plot() all derive from analysis_dir, so all inherit the gap.

[SPEC] Let the run_id tree be nested. Two candidate fixes: (A) add an optional exp_group / sub-path component the profile can set (e.g. output_root='experiments' + run_group='rsl_rl/albc_trpo_teacher'), so analysis_dir = out_root / run_group / run_id / 'analysis' / id; OR (B) resolve the run's existing canonical dir (the one holding the train symlink) and place analysis/ inside it, mirroring how eval already nests. (A) is cleaner/declarative but per-exp (student runs need a different group); (B) auto-discovers and always matches eval's location -> preferred. Whichever: analysis/ MUST land as a sibling of eval/ inside the existing run_id dir.

[EVIDENCE] this analysis (20260602-192051-diagnose): getter put report.md at the flat path; correct location verified by the pre-existing eval tree at experiments/rsl_rl/albc_trpo_teacher/260525_232805_trpo_main_teacher/eval/static_* and the train->../../../../logs symlink (rule 03 函정2 run_id-tree marker). Files relocated manually; getter still wrong for next run.

[STATUS] proposed
