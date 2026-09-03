# G0-I met: thruster_dead_frac dead atom + exposure unit test, incumbent bit-identical at 0 (commit 4cef724, implementer agy)

- id: finding/311 · date: 2026-09-04 · author: session-mac-fable
- project: albc · harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: decision
- confidence: high · status: resolved
- verified: none · keywords: G0-I, fault sampler, dead atom, thruster_dead_frac, agy, retrain
- summary: G0-I gate met 2026-09-04: FaultInjectionCfg.thruster_dead_frac (default 0.0) + 5 lines in sample_thruster_health; no extra RNG draw at 0 so the incumbent sampler is bit-identical (asserted by test). tests/test_fault_sampler_exposure.py 4 passed (closed-form q=s*p0*d numbers within 0.5 pp at s=1 and s~U(0,1), all-healthy at s=0) + 42 existing fault/config tests. p0=0.15 is a launch-config value, not a code default. Implemented by agy (gemini) after the Claude agent hit 529 and codex returned 404; user: no codex for now. G0-C not queued.

# G0-I met: dead-atom sampler mechanism + exposure unit test (commit 4cef724)

2026-09-04 00:2x. Gate **G0-I** of `retrain-simtoreal-2026-09` (PLAN §6 row G0-I, §5 item (2)).

## What changed
- `constrained_albc/envs/main/config.py` — `FaultInjectionCfg.thruster_dead_frac: float = 0.0` (new). A FAILED channel is fully dead (health exactly 0.0) with this probability, else residual health ~ U(`thruster_health_range`).
- `constrained_albc/envs/main/mdp/faults.py` — 5 lines at the end of `sample_thruster_health`: `if dead_frac > 0.0:` draw a dead mask and zero the residual there. **At `dead_frac == 0` no extra RNG draw happens**, so the incumbent output is bit-identical (asserted).
- Item (1), p₀ = 0.15, is a launch-config VALUE on the existing `thruster_fail_prob` — no code default changed. `fault_severity` curriculum untouched (item (3)).

## Test
`/isaac-sim/python.sh -m pytest tests/test_fault_sampler_exposure.py -q` → **4 passed** (fixed severity 1 with p₀ 0.15, d 0.5 → q 0.075: P(≥1 dead)/P(≥2)/P(exactly m3∧m4) within ±0.5 pp of 37.4 % / 6.89 % / 0.41 %; severity-integrated s~U(0,1) P(≥2) within ±0.5 pp of the quadrature value ≈ 2.42 %; severity 0 → all 1.0; dead_frac 0 → `torch.equal` with the incumbent three-line sampler at the same seed). Existing `tests/test_fault_dr.py`, `test_fault_fixed_health.py`, `test_faults.py`, `test_config_equivalence.py` → 42 passed.

## Provenance
Implementation authored by **agy** (gemini-3.1-pro-high, effort high, 15 KB inline prompt: faults.py, config.py excerpt, call sites, PLAN §5/§6 rows). The Claude executor agent first dispatched for this gate hit API 529 and was shut down; codex 0.152.x/0.153.0 returned HTTP 404 from `chatgpt.com/backend-api/codex/*` on both machines, and the user then instructed not to use codex for now. The Mac session applied the diff verbatim, adapted only the test to the repo by-path import pattern (`test_doraemon.py` style), ran the tests, committed.

## Not done / next
G0-C (paired probe) is queue-only and NOT queued — user: "plan only, do not train yet". G0-J will carry `thruster_fail_prob 0.15` + `thruster_dead_frac 0.5` in the §5 delta.
## Comments
