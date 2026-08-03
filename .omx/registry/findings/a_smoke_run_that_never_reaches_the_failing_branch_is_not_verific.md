---
title: "A smoke run that never reaches the failing branch is not verification: size it to the branch, or prove the fix by removing it"
tags: []
created: 2026-08-03T14:34:01.358561
updated: 2026-08-03T14:34:01.358561
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# A smoke run that never reaches the failing branch is not verification: size it to the branch, or prove the fix by removing it

## The incident (2026-08-03, obs4 Phase D)

A gen-2 teacher config was smoke-tested at 64 envs x 2 iterations. It passed, its saved
`params/env.yaml` recorded the expected `observation_space: 76`, and that was reported as
verified. The real 4096-env launch then died at iteration 1.

The failing write sat behind `if pending.any():` — it only executes once an episode reset
re-arms `_extra_reset_pending`. A 64-env, 2-iteration run never resets. The smoke
exercised everything EXCEPT the branch that was broken, while looking like a clean pass.

## Two rules that follow

**1. Size the smoke to reach the branch you are worried about.** Ask what has to HAPPEN
for the risky code to execute — a reset, a termination, a curriculum step, a checkpoint
save, a log interval — and make the smoke big enough or long enough to make it happen. A
smoke that only proves "it starts" proves that and nothing else, so claim only that.

**2. Prove a fix by removing it.** The definitive check is the A/B at the integration
level: same command, guard in vs guard out. Here 512 envs x 15 iterations was clean with
the guard and reproduced the exact `RuntimeError` at iteration 7 without it. That
establishes the fix is what made the difference, which a passing rerun alone never does —
the rerun could be passing for any reason, including a shorter run.

This is the integration-level twin of the unit-test rule (`feedback-test-must-be-able-to-fail`):
watch it fail before trusting it, whether "it" is an assertion or a training launch.

