---
title: "RETRACTED — barrier_alpha is 0.02 not 0.05 (this claim was WRONG)"
tags: ["retracted", "barrier_alpha", "constraint_trpo", "superseded"]
created: 2026-06-07T02:54:26.487897
updated: 2026-06-07T02:58:00.000000
sources: ["diagnose-20260607-113942"]
links: ["barrier_alpha_runtime_0_05_agent_cfg_injects_over_ctor_default_0.md"]
category: decision
confidence: low
schemaVersion: 1
---

# RETRACTED — this page's claim (barrier_alpha=0.02) was WRONG

**Do not use this page. The claim is incorrect and has been superseded.**

The original claim here — that runtime `barrier_alpha = 0.02` and the docs' 0.05 was drift —
was based on reading only the **ctor signature default** (`constraint_trpo.py:65`). That is NOT
the runtime value. The resolved agent config `rsl_rl_ppo_cfg.py:198 barrier_alpha=0.05` is
**injected over** the ctor default, and the per-run resolved record `params/agent.yaml:127`
confirms `barrier_alpha: 0.05`. So the runtime value is **0.05**, the docs were RIGHT, and this
"correction" was the actual error (rule03 "Verify Implementation, Not Name" — verify the resolved
config, not the function signature).

Correct page: [[barrier_alpha_runtime_0_05_agent_cfg_injects_over_ctor_default_0]].

The `J_C/d_k = 0.944` binding conclusion (analysis `diagnose-20260607-113942`) is unaffected
either way — it is computed in the slack regime as `J_C = d_k - margin`, alpha-independent.
