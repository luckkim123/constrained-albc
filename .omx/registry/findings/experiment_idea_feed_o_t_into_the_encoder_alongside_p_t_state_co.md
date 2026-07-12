---
title: "experiment idea: feed o_t into the encoder alongside p_t (state-conditioned z, RMA-style) instead of p_t-only encoder input"
tags: ["encoder", "rma", "experiment-idea", "latent"]
created: 2026-07-08T02:28:39.004317
updated: 2026-07-08T02:28:39.004317
sources: []
links: []
category: convention
confidence: medium
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# experiment idea: feed o_t into the encoder alongside p_t (state-conditioned z, RMA-style) instead of p_t-only encoder input

EXPERIMENT IDEA (proposed 2026-07-08, NOT yet designed/run): feed o_t into the encoder alongside p_t, instead of the current p_t-only encoder input.

## Current architecture (verified)
The main-task asymmetric encoder (`envs/main/encoder/actor_critic_encoder.py`) takes ONLY the privileged obs as input: `_encode` (`:206-216`) reads `obs[self._privileged_key]` (= p_t, 27D) -> static min-max norm -> MLP[256,128,64] elu -> LayerNorm -> softsign -> z(9). The actor then sees `cat[normalize(o_t 69D), z 9D]`; the actor already sees o_t directly. So z is designed to carry ONLY the hidden physics (privileged) that o_t lacks -- a pure RMA/HORA-style "environment factor" latent.

## The idea
Add o_t (or a subset / its history) to the encoder input so z is `encode(o_t, p_t)` rather than `encode(p_t)`. Motivation: in RMA (Kumar 2021) and much follow-up, the adaptation/context encoder is fed the recent state-action history, not pure physics params, because z should capture the CURRENT dynamics context, not just static parameters. A p_t-only encoder cannot condition z on the vehicle's present motion state; adding o_t lets the encoder produce a state-conditioned latent.

## Design tensions to resolve (why this is non-trivial, not a one-liner)
1. Redundancy risk: the actor ALREADY sees o_t directly (`cat[o_t, z]`). If the encoder also sees o_t, z may collapse into a re-encoding of o_t rather than a privileged-physics summary -- wasting latent capacity and defeating the asymmetry. Watch for z becoming actor-redundant (encoder z-sweep should still show physics-param sensitivity, not just o_t sensitivity).
2. Normalization mismatch: encoder currently uses STATIC min-max bounds tied strictly to `encoder_input_dim` (`:142-145` ValueError guard) and derived from DR ranges (`priv_obs_bounds.py`). o_t is NOT DR-derived -> it has no min-max DR bounds; it is EmpiricalNorm-normalized on the actor path. Mixing a DR-min-max block (p_t) with a running-stat block (o_t) in one encoder input needs a deliberate two-normalizer design (or route o_t through EmpiricalNorm and p_t through static min-max, then concat).
3. Existing partial hook: `encoder_obs_indices` / `_enc_obs_indices` (`:125,134`) already selects encoder input by index -- today within p_t. This is the natural wiring point to extend the encoder input to include o_t dims, but the selection currently assumes a single obs tensor; feeding o_t means concatenating two obs groups before selection.
4. Student distillation: the TCN/GRU student reconstructs z from o_t history. If z already depends on o_t, the student's target changes -- re-examine `student/` collector/teacher.
5. Rule 03 (No-Encoder-Auxiliary-Losses): this is an INPUT change, not an aux loss -- allowed. Do NOT pair it with a reconstruction/contrastive loss (that path failed: decoder ignores z, z collapses).

## Status / gate
Idea only. Needs a design (which o_t dims: full 69D vs proprio-only vs history; single vs dual normalizer; z-dim revisit) then a baseline comparison (does state-conditioned z improve attitude tracking / robustness vs p_t-only, without z collapsing to o_t re-encoding). Separate experiment from the p_t-slim / DR-offset-prune / buoy-split changes (all of which shrink p_t; this changes what feeds the encoder). Provenance: session project-obs-space-doc-qa-260708; related doc constrained-albc/docs/reference/observation-space.md section 5 (asymmetric consumption).

