---
title: "DORAEMON/kl_step final value 0.0000 is a sparse-logging artifact, NOT a frozen curriculum"
tags: ["doraemon", "kl_step", "sanity-gate", "tensorboard", "sparse-logging", "engine-output"]
created: 2026-07-16T07:48:28.708915
updated: 2026-07-16T07:48:28.708915
sources: ["diagnose-20260716-164016"]
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# DORAEMON/kl_step final value 0.0000 is a sparse-logging artifact, NOT a frozen curriculum

TRAP: reading DORAEMON/kl_step final scalar as 0.0000 and concluding the curriculum froze / trust region collapsed is WRONG. The scalar is only written on the 250-iter curriculum steps (step_interval=250); between steps it logs 0. On P-B1 (trpo_biasema_260715_142543) the full 5000-point trajectory shows value=0.1200 at every sampled curriculum step (iter 500/1000/.../4500), max=0.1200, nonzero count 18/5000. The trust region stayed PINNED at the configured kl_ub=0.12 (config.py:544) the whole run. This is the exp-analyze 'empty cell is a hypothesis not a fact' rule applied to a sparse scalar: to check the kl_step sanity gate, pull the trajectory and look at the nonzero (curriculum-step) samples, never the final value. Same pattern will bite any DORAEMON per-step scalar (entropy_before/after also only move on curriculum steps). Found during report diagnose-20260716-164016.
