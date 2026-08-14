---
title: "eval.py static --ood appends a fifth DR level and unpairs every cross-run comparison at soft/medium/hard"
tags: ["eval", "pairing", "ood", "decision-floors", "protocol", "instrument"]
created: 2026-08-14T15:07:00.531182
updated: 2026-08-14T15:07:00.531182
sources: ["diagnose-20260814-235911"]
links: ["eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# eval.py static --ood appends a fifth DR level and unpairs every cross-run comparison at soft/medium/hard

Two evals of the same plant are comparable under the decision floors only if their per-env draws match,
and the `--ood` flag silently breaks that. `eval.py:1302` appends "ood" to `DR_LEVELS` under the flag,
so an `--ood` eval runs a five-level sweep while a stock one runs four. Measured 2026-08-14 on the
incumbent teacher against two fresh evals, counting `dr_*` / `fault_injection` / `target_*` keys that
match elementwise out of 27:

| level | vs the `--ood` eval | vs a protocol-matched re-run |
|:--|:--|:--|
| none | 27/27 | 27/27 |
| soft | 4/27 | 27/27 |
| medium | 4/27 | 27/27 |
| hard | 4/27 | 27/27 |

`none` survives because its `dr_*` are constant across envs by construction (every key n_unique = 1),
so it is paired no matter what the RNG did. Everything else is not.

WHY IT MATTERS AND HOW IT FAILS. The floors are PAIRED-ONLY. An unpaired delta is not "a weaker
result", it is unadjudicable: the numbers still print, `floor_verdict` still returns something, and
nothing warns. Reaching for the newest existing eval as a baseline is the natural move and it is what
produces the failure.

THE CHECK, before any floored cross-run comparison: load both `data_<level>.npz` and assert the
`dr_*` / `fault_injection` / `target_*` keys are elementwise equal at every level you intend to
adjudicate. Four matches out of 27 is the signature of a protocol difference, not of noise.

THE FIX is cheap: re-run the baseline under the same flags as the new evals (8.6 min for 64 envs x 4
levels on the workstation). Do not try to salvage the mismatched pair by restricting to `none` unless
`none` is genuinely the level the question lives at.

BY-PRODUCT WORTH KEEPING: the same checkpoint scored twice, once with `--ood` and once without, moved
`none` att_norm ss_error 0.5102 -> 0.5070 and roll ss_error 0.4453 -> 0.4479. That bounds this
instrument's own variation at `none` at about 0.003 deg, i.e. 3% of the 0.10 deg floor -- so floored
verdicts clear instrument noise by more than an order of magnitude. roll n_gt20 is much looser on the
same pair, 4.33 -> 2.67 envs, so treat env-count metrics as the noisy ones.

Sibling trap, different cause, same symptom:
[[eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr]].

