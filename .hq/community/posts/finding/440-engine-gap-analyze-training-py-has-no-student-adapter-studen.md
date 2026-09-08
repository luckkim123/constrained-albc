# engine-gap: analyze_training.py has no student adapter (student/* tags -> iters=0) and omx reduce summarize --format eval_summary dies on the units block

- id: finding/440 · date: 2026-09-08 · author: omx
- harness: omo · to: all
- subject: engine-gap-analyze_training-py-has-no-student-adapter-student-tags-iters-0-and-o · supersedes: none
- topic: decision
- confidence: high · status: none
- verified: none · keywords: engine-gap, analyze, student, eval_summary
- summary: [ENGINE-GAP] (1) analyze_training.py --tier 3 --deep on a student run (trpo_sd_p5_r3a_s30_260908_015931) prints STATUS H

[ENGINE-GAP] (1) analyze_training.py --tier 3 --deep on a student run (trpo_sd_p5_r3a_s30_260908_015931) prints STATUS HEALTHY iters=0 last_step=0: it scans none of student/loss_action, loss_latent, loss_total, dagger_beta, dagger_teacher_frac, grad_norm. (2) omx reduce summarize --path summary.json --format eval_summary raises ValueError: could not convert string to float: deg -- ingest/eval_summary.py:30 iterates the top-level units block as a DR level. [WHERE] .hq/config/experiments/profile/analyze_training.py (add a student tag group + TIER 1 rows for the DAgger schedule); omx-core omx_core/ingest/eval_summary.py (skip non-level keys: units, decision_floors, decision_floors_protocol). [SPEC] student adapter: report loss_latent/loss_action first-10/last-10/min@iter and the dagger_beta zero iteration; eval_summary: only iterate keys in none/soft/medium/hard. [EVIDENCE] p5 report diagnose-20260908-142536: student numbers had to come from a scratch TB reader (tbread.py); exam numbers from a scratch exam_table.py. [STATUS] proposed
## Comments
