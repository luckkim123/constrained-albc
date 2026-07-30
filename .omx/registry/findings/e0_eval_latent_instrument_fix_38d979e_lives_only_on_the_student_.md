---
title: "E0 eval latent instrument fix 38d979e lives only on the student branch, not main"
tags: ["eval", "instrument", "student", "latent", "git", "integration", "albc", "tech-debt"]
created: 2026-07-29T08:48:16.859015
updated: 2026-07-30T05:03:34.314667
sources: ["diagnose-20260729-172500"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
blocked-on: "User decision 2026-07-29: carry it in the eventual merge of exp/student-distill-eint into main rather than cherry-picking it alone, because main is 31-53 commits behind and lacks six other analysis/ changes that would leave it half-patched. The branch is now PUSHED (origin/exp/student-distill-eint, verified by git branch -r --contains 38d979e), so the fix is backed up and fetchable from any machine. Not urgent -- nobody is checked out on main. Becomes urgent the moment any campaign branches from main or runs a student latent eval from it."
---

# E0 eval latent instrument fix 38d979e lives only on the student branch, not main

Commit `38d979e` ("fix(eval): student latent instrument must delegate, not re-run the encoder") is
NOT on `main`. As of 2026-07-29 it exists only on branch `exp/student-distill-eint`.

## Why this matters

`eval.py`'s student-latent diagnostic reimplemented the policy forward pass and dropped observation
normalization on the TCN branch. Every student latent number measured with the pre-fix instrument is
wrong, which is what retracted the earlier "no correction-side experiment remains" verdict on the
DAgger lead. The fix delegates to `last_l_hat` instead (net -12 lines) and ships a guard,
`tests/test_student_eval_latent_instrument.py`, confirmed to bite on the pre-fix source. Suite after
the fix: 377 passed / 9 skipped.

**Any eval of student latents run from a `main` checkout is therefore measuring nothing physical
until this commit lands there.**

## Decision 2026-07-29 (user): carry it in the eventual merge, do NOT cherry-pick

Cherry-picking it alone was considered and rejected. `main` is 31 commits behind
`exp/student-distill-eint` and 53 behind `exp/ftc1-severity-init`, and in `constrained_albc/analysis/`
alone it lacks six other changes:

| file | lines behind |
|:--|--:|
| _analyze/paired.py | +134 (absent) |
| _analyze/recompute_metrics.py | +68 (absent) |
| _analyze/recompute_plots.py | +25 |
| _analyze/export.py | +6 |
| compare.py | +19 |
| eval.py | +96 total, of which 38d979e is a part |
| student_policy.py | +10 |

A lone cherry-pick would fix the instrument while leaving `main` without the analysis tooling that
consumes it -- a half state that is not usable anyway. Nobody is checked out on `main` (both working
trees sit on experiment branches), so the exposure is latent rather than active.

## For whoever integrates

The cherry-pick was verified to apply without conflict if the decision is revisited:
`git merge-tree --write-tree --merge-base 38d979e^ main 38d979e` returns CLEAN.

Checklist at merge time: confirm `38d979e` is an ancestor of the merged `main`
(`git branch --contains 38d979e` must list `main`), and confirm
`tests/test_student_eval_latent_instrument.py` exists and passes there. If a future campaign branches
from `main` before that merge, it inherits the broken instrument -- branch from the integrated tip or
cherry-pick then.

---

## Update (2026-07-29T08:54:22.454451)

UPDATE 2026-07-29 18:00: the branch is now pushed. `origin/exp/student-distill-eint` exists and
`git branch -r --contains 38d979e` lists it, so the fix and its guard test are no longer single-copy
on one machine. Before this push the deferral had no backup at all -- deciding to carry a fix in a
later merge only works if the branch holding it survives, so pushing is part of that decision, not a
separate chore.

---

## Update (2026-07-30T05:03:34.314667)

## RESOLVED 2026-07-30: the merge the user's decision named has landed, so 38d979e is on main

[FINDING] The 2026-07-29 user decision was to carry this fix in the eventual merge of exp/student-distill-eint into main rather than cherry-picking it alone. That merge happened; 38d979e is now an ancestor of both main and origin/main, so the fix no longer lives only on the branch and the condition that would have made it urgent (a campaign branching from main, or a student latent eval run from main) is satisfied in advance.

[EVIDENCE] Verified 2026-07-30 in /workspace/constrained-albc: `git branch -a --contains 38d979e` returns main, remotes/origin/exp/student-distill-eint and remotes/origin/main; `git merge-base --is-ancestor 38d979e main` exits 0. main is at 9ef4cf6 ("feat(student): DAgger mixes policies, not action vectors (dagger_mix=select)"), the tip of that merge.

[CONFIDENCE] HIGH

The six other analysis/ changes that made a lone cherry-pick a half-patch came across in the same merge, which is exactly why the user chose the merge route over the cherry-pick. Nothing further is pending on this page; status moved from needs-apply-before-retrain to resolved.

For anyone auditing an OLD checkpoint's eval: the instrument fix changes what the student latent diagnostic measures, so a latent readout produced BEFORE 38d979e is not comparable to one produced after. That comparability caveat outlives the git question -- see the audit-the-instrument lesson (the pre-fix diagnostic reimplemented the policy forward and dropped obs normalization, so its "observability floor" and DAgger verdicts measured nothing physical).

