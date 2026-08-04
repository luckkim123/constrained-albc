---
title: "engine-gap: the analysis engine and omx reduce are both unusable on student distillation runs"
tags: ["engine-gap", "adapter", "student", "distillation", "omx", "profile", "albc"]
created: 2026-07-29T07:26:31.168314
updated: 2026-08-04T04:32:23.588809
sources: ["diagnose-20260729-161459"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# engine-gap: the analysis engine and omx reduce are both unusable on student distillation runs

[ENGINE-GAP] Three separate limits block engine-grounded analysis of a Stage-2 distillation run; all three were hit in analysis diagnose-20260729-161459 and worked around by hand.

1. [WHERE] .omx/profile/analyze_training.py, TIER 1 step-axis resolution.
   [SPEC] It returns 'STATUS: HEALTHY iters=0 last_step=0' on a student run that has 1000 logged samples per tag, and emits no [DIAGNOSIS]/changepoint/plateau/regime line. It resolves auto targets (iter, grad_norm, loss_action, time_collect, time_train) but cannot find the iteration axis under the `student/` namespace. Teach it the student namespace so tier-1/3 diagnosis works, or have it loud-fail 'unsupported run type' rather than report HEALTHY with iters=0.
   [EVIDENCE] /isaac-sim/python.sh .omx/profile/analyze_training.py <b4b run dir> --tier 3 --deep.

2. [WHERE] .omx/profile/metrics.yaml `groups`.
   [SPEC] Five of the seven declared groups (reward_decomp, trpo, critic, constraint, doraemon) cannot exist in a distillation run, which freezes the teacher actor and fits only the latent -- the run logs exactly 8 scalar tags, all under `student/`. A sixth, `encoder`, IS applicable but is instrumented from the eval side (latent env-variance ratio, in-loop MSE), not from the teacher's Encoder/* TB tags. Every student report therefore fails report-coverage for structural reasons. Add a run-type-aware group set (e.g. groups_student: distillation_loss [student/loss_latent, student/loss_action, student/loss_total], dagger [student/dagger_beta], throughput [student/time_train, student/time_collect], latent_fidelity [ratio, in-loop MSE, per-dim collapse]) so the lint measures something real for this run type.
   [EVIDENCE] report-coverage on diagnose-20260729-161459 returns missing_groups = [reward_decomp, trpo, critic, encoder, constraint, doraemon] with tracking at 4/4 and missing_sections empty.

3. [WHERE] container environment, not omx source.
   [SPEC] `omx reduce tb-final --format tensorboard` cannot run here at all: the system python3 that owns omx_core has no tensorboard, and /isaac-sim/python.sh (which has tensorboard) has no pandas, which omx_core/reduce/summarize.py imports at module level. Putting omx_core on PYTHONPATH for the isaac interpreter gets past the import of omx_core and then dies on pandas. Either make the pandas import lazy (only summarize needs it, tb-final does not) or document the supported interpreter. Workaround used: a scratch script under .omx/scratch/<sid>/py/tb_window_means.py replicating tb-final's trailing-window mean.
   [EVIDENCE] both invocations and their tracebacks, 2026-07-29.

[STATUS] proposed

---

## Update (2026-08-04T04:32:23.588809)

## 4th limit, hit 2026-08-04 (analysis diagnose-20260804-132500)

[WHERE] constrained_albc/analysis/_analyze/recompute_metrics.py, `_per_env_ss_stats`.
[SPEC] It computes the per-env steady-state array internally (`per_env_mean`, `per_env_std`) and then
returns only the aggregated scalars, so the per-env vector is unreachable by any consumer. A
heavy-tail campaign needs that vector: the natural causal test for a distillation regression is
"do the envs with the worst latent error have the worst control error", and it cannot be run.
Reproducing the segment/settled-window logic outside the repo to recover the array is exactly the
duplicated-code-path failure that 38d979e already cost this campaign, so the test was DROPPED rather
than answered with a reimplementation. Return the per-env arrays alongside the scalars (or expose a
`per_env=True` variant) and the test becomes a one-liner.
[EVIDENCE] Phase E: the fallback available without repo logic -- terminated / time_to_failure -- shows
the 2 dead envs at hard rank 26/64 and 9/64 by latent RMSE (median 0.2566, max 0.4984), which is
suggestive but far weaker than the per-env correlation the question actually needs.

Also re-confirmed unchanged from items 1-2 above: `analyze_training.py --tier 3 --deep` still returns
STATUS: HEALTHY / iters=0 / last_step=0 on a student run with 1000 logged samples per tag, emitting no
DIAGNOSIS / changepoint / plateau / regime line; and 5 of the 7 profile groups (reward_decomp, trpo,
critic, constraint, doraemon) remain structurally absent -- verified this time by dumping the raw tag
set, which is exactly 9 scalars all under `student/`.

