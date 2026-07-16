---
title: "P-A8 (perflb200 more-iters 5000->8000) closed the deployment-OOD DR gap exactly as predicted, at a quantified nominal-tracking cost offset by heavy-tail reduction"
tags: ["doraemon", "dr-anatomy", "p-a8", "perflb200", "deployment-ood", "curriculum-budget"]
created: 2026-07-15T19:00:35.530450
updated: 2026-07-15T19:00:35.530450
sources: ["diagnose-20260716-035505"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# P-A8 (perflb200 more-iters 5000->8000) closed the deployment-OOD DR gap exactly as predicted, at a quantified nominal-tracking cost offset by heavy-tail reduction

# P-A8 result (max_iterations 5000->8000, fresh run not resume, same perflb200 config lb=200)

[FINDING] The DR-anatomy prediction from perflb200_final_dr_anatomy... was CONFIRMED exactly: all 20
DORAEMON params, including the 3 previously time-limited deployment-relevant ones (ocean_current_strength,
obs_noise_scale, payload_cog_offset_xy_u, only 16-18% expanded at iter 5000), reached Beta(1.00, 1.00) —
perfectly uniform, full config-ceiling range — by iter 8000. The deployment-OOD gap this session's
DR-anatomy analysis flagged is now fully closed within the current config bounds.
[EVIDENCE: doraemon_state.pt dist_a/dist_b, all 20 dims, run trpo_perflb200-moreiters_260715_195227,
independently re-verified via torch.load by report-reviewer]

[FINDING] Cost at the fair `none` comparison: roll ss_error +31% (0.395->0.516), pitch +61%
(0.169->0.272), CV and jitter both up. This is the expected DR-robustness tradeoff (training on the
fully-expanded curriculum costs narrow-distribution precision), not a policy regression.
[EVIDENCE: eval/static_260716_034515 vs eval/static_260715_141532 summary.json none level, independently
recomputed by report-reviewer, exact match]

[FINDING] Benefit offsetting the cost: heavy-tail transient-peak count (n_gt20) dropped sharply — roll
21.3->9.3 (-56%) at `none`, held better at `hard` too (8.3->6.3). Fewer catastrophic per-env outliers
even under the harder, fully-expanded curriculum.
[EVIDENCE: same summary.json pair, n_gt20 field]

[FINDING] NO over-widen-backfire (the documented failure mode this probe was guarded against, wiki
doraemon_over_widens_then_oscillates...): success settled AT alpha (0.50), not below it — the backfire
signature requires success dropping below alpha (that page's own example ended 0.368 < 0.5). ess_ratio
IMPROVED to 1.00 (from 0.75). mode stayed 0 throughout (no re-stall). barrier_penalty max spike (0.211)
was inherited from before iter 5000, not a new event. report-reviewer independently verified this
inference is evidence-anchored, not overreach.
[EVIDENCE: engine deep output, success/ess_ratio/mode/barrier_penalty lines, both runs]

[FINDING] Engineering note: resuming via --resume/--load_run/--experiment_name failed twice for a
run_group-nested checkpoint — isaaclab's get_checkpoint_path (source: isaaclab_tasks/utils/parse_cfg.py)
only os.scandir's ONE level under log_root_path, cannot reach a run living two levels deep
(log_root_path/run_group/run_id); folding the group into --experiment_name also failed (CLI override did
not propagate to agent_cfg.experiment_name, root cause unresolved). Fresh run used instead per 3-strike
rule — this is arguably cleaner anyway (no resume-mechanism confound), but a future genuine resume need
on a grouped run will hit the same wall until this is investigated.
[EVIDENCE: two failed launch attempts, error "No runs present in the directory... match:", this session]

# Decision

The deployment-OOD DR-difficulty question the user raised this session (2026-07-15, "is perflb200 hard
enough for deployment or did it stop too easy?") is now answered with a completed measurement: the config
ceiling is fully reachable and was reached. Whether the none-level precision cost is an acceptable price
for the heavy-tail benefit (i.e. whether to adopt max_iterations=8000 as standing config vs find a middle
ground) is a next-week design decision — deferred per this week's token-saving run+analyze+eval-only mode.
report-reviewer found one numeric error (generalization-section roll spread mis-transcribed as "3.3x->3.3x
flat" vs the correct 4.2x->3.3x narrowing) — corrected via RE-analysis before this wiki capture; verdict
approve after the fix.

