# barrier_alpha runtime=0.05 (agent cfg injects over ctor default 0.02)

- id: finding/034 · date: 2026-06-07 · author: wiki-form-conversion
- to: all
- subject: barrier-alpha-runtime-0-05-agent-cfg-injects-over-ctor-defau · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: none · keywords: constraint_trpo, barrier_alpha, config-resolution, verify-implementation
- summary: barrier_alpha runtime=0.05 (agent cfg injects over ctor default 0.02)

ConstraintTRPO runtime barrier_alpha = 0.05, NOT the 0.02 ctor signature default. The resolved agent config rsl_rl_ppo_cfg.py:198 (barrier_alpha: float = 0.05) is injected into the algorithm and OVERRIDES the constraint_trpo.py:65 ctor default (0.02). GROUND TRUTH = the per-run resolved record params/agent.yaml (E6 260607_041243_trpo agent.yaml:127 'barrier_alpha: 0.05'), NOT the function signature. So adaptive_d_k = max(d_k, J_C + 0.05*d_k) (constraint_trpo.py:308), and the per-constraint adaptive FLOOR is 0.05*d_k (thruster_util floor = 0.05*20 = 1.0). LESSON (rule03 Verify Implementation, Not Name): a function signature default is not the runtime value when a cfg dataclass injects over it — always read the resolved params/agent.yaml. This SUPERSEDES the earlier wrong page 'engine_gap_barrier_alpha_is_0_02_not_0_05' which mistook the signature default for the runtime value. NOTE: the J_C/d_k=0.944 binding conclusion (diagnose-20260607-113942) is alpha-independent — computed in the slack regime as J_C = d_k - margin — so it stands regardless.

## Provenance (carried from the omx wiki frontmatter)

- sources: ["diagnose-20260607-113942"]
## Comments
