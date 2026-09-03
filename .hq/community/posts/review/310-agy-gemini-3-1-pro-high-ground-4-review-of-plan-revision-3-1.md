# agy (Gemini 3.1 pro-high) ground-4 review of PLAN revision 3.1: 3 BLOCK / 3 MAJOR / 1 MINOR -- two findings duplicate finding/309 independently (40 N coefficient, linear-only R-1 readout), two accepted into 3.3, two rejected on config.py evidence, one partly; two-family gate met

- id: review/310 · date: 2026-09-03 · author: session-mac
- harness: omo · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: history
- confidence: medium · status: resolved
- verified: yes · keywords: agy, gemini, ground-4, two-family, retrain-simtoreal-2026-09, review
- summary: Second vendor family. Files had to be INLINED (file-pointing prompts time out or return files-missing); 64 KB inline returned in 3m57s. Findings: axis-naming objection rejected (pitch = rotation about sim y, rotate_imu maps the IMU into that frame, m0 probe verified); fixed-health index objection rejected (config.py:130-137 orders sim channels as m0..m5); 40 N coefficient and linear R-1 readout confirmed and already fixed in 3.2 via finding/309; delay-row/G0-B contradiction and the G0-B [1.3x,2x) gap accepted into 3.3; deadband inertness asserted in G0-J. codex and agy did not overlap; both found the 50->40 N constant that finding/309 also found.

Second vendor family for the retrain plan. Reviewer: agy backend, `gemini-3.1-pro-high`, `--effort high`, ground 4, 2026-09-03. Object reviewed: the REVISION 3.1 text of `PLAN.md` (the 3.2 edits landed while this call was in flight), `finding/305`, and the incumbent `deployed_env.yaml` — all three INLINED into one 64 KB prompt. Wall time 3 m 57 s.

## How the call had to be made (operating fact, not a footnote)

Three attempts. (1) Prompt pointing at file paths in a workdir that also held the 444-post community mirror: timed out at the wrapper's 297 s ceiling. (2) Same prompt in a three-file workdir: returned in 4 m 40 s with a single BLOCK saying the three files "are missing from the accessible filesystem". (3) Files inlined: returned the review below. So for this backend the unit of a prompt is inlined text, not file paths — the "≤ 5 files" rule from `handoff/304` was the wrong axis; the right one is "inline, and keep the total under what fits the ceiling".

## Verbatim output

```
[BLOCK] [PLAN line 15, 51] The plan dismisses the "wrong axis" lead by claiming a moment about the +y forward axis (12 o'clock) is physical pitch, but rotation about the forward axis is physically roll.
Fix: Reinstate the axis mismatch finding; since m0/m3 are at ±x (3/9 o'clock), their differential thrust provides roll, meaning the sim's assignment of them to pitch (My) is physically swapped.
VERDICT: BLOCK

[BLOCK] [PLAN line 110, 150] The m3-dead/m4-excluded exam vector `--fault_fixed_health 1,1,1,0,0,1` assumes physical indices, but `expected_thruster_order` maps policy actions to `[3,2,4,0,5,1]`, so applying this mask to the action space wrongly kills m0 and m5.
Fix: Change the fixed health mask to `0,1,0,1,1,1` so it correctly targets m3 (index 0) and m4 (index 2) in the policy's action space.
VERDICT: BLOCK

[BLOCK] [PLAN line 128] The R-1 protocol incorrectly compares the effective moment to a sim baseline of 0.145 m × 50 N, but the configuration sets `thrust_coefficient: 40.0`, meaning the actual linear sim baseline is 0.145 m × 40 N.
Fix: Correct the sim expected value in R-1 to 0.145 m × 40 N (5.8 N·m) to match `deployed_env.yaml` and prevent a false-positive tuning gap.
VERDICT: BLOCK

[MAJOR] [PLAN line 95, 111] Section 5 unconditionally hardcodes `(0, 1)` delay into the Phase 1 retrain baseline, but Section 6's G0-B gate treats it as a go/no-go decision that might drop it, creating a contradiction in the baseline.
Fix: Explicitly mark `control_delay_steps` in Section 5 as a `[DECISION-REQUIRED: delay-range]` dependency tied to the G0-B outcome.
VERDICT: REVISE

[MAJOR] [PLAN line 111] Gate G0-B's pass criteria are unfalsifiable in the middle ground because they define actions for degradation ≥ 2.0x and < 1.3x, leaving the [1.3x, 2.0x) range undefined.
Fix: Provide a conclusive decision rule for delay degradation falling into the [1.3x, 2.0x) gap.
VERDICT: REVISE

[MAJOR] [PLAN line 128] The R-1 protocol probes multiple command levels but collapses the readout into a single ratio `M(u)/u`, which assumes linearity and completely masks any quadratic thrust-curve shape discrepancy.
Fix: Change the R-1 readout to explicitly evaluate the measured `M(u)` against both linear and quadratic models of the command `u` to identify the shape.
VERDICT: REVISE

[MINOR] [PLAN line 61, 97] The plan assumes `thrust_deadband 0.075` is inert because `enable_thrust_curve` is false, but if the linear sim model still applies it, it will cause double-compensation since the deployment mixer also inverts it.
Fix: Set `thrust_deadband: 0.0` explicitly in the Section 5 config delta to guarantee it cannot interfere with training.
VERDICT: REVISE

```

## Disposition (Claude session, against the record)

| # | agy finding | Verdict | Evidence / action |
|:--|:--|:--|:--|
| 1 | BLOCK — rotation about the forward (12 o'clock) axis is roll, so ±x thrusters give roll, not pitch | **REJECTED** (naming, not physics) | "pitch" in this program is rotation about the sim y axis (Isaac roll-x/pitch-y/yaw-z); `rotate_imu` (+102°, pitch negation, `build_proprio.py:84-94`) puts the robot IMU in that frame; r × F for a thruster at ±x pushing ±z is a moment about y; the m0 probe moved the "pitch" channel with "roll" unchanged (`deployed_tam.json`, `finding/305` §1). Same objection as `handoff/304`, raised by a second independent reader → a convention sentence is now in D-1 so it is not raised a third time |
| 2 | BLOCK — `--fault_fixed_health 1,1,1,0,0,1` uses physical indices while `expected_thruster_order [3,2,4,0,5,1]` maps actions, so it kills m0 and m5 | **REJECTED** | `config.py:130-137`: "channels ordered to match robot firmware ESC wiring, m0..m5 — m0, m3 vertical; m1, m2, m4, m5 horizontal", achieved by `_reorder_columns(_BASE_ALLOCATION_MATRIX, _ESC_CHANNEL_ORDER)`. Sim index j IS m_j; `1,1,1,0,0,1` kills m3 and m4. `expected_thruster_order` is the deployment-side ESC order derived from the matrix + measured channel map (`deployed_tam.json`), not a permutation the sim applies to health. Noted in G0-A |
| 3 | BLOCK — R-1 compares to 0.145 m × 50 N but `thrust_coefficient` is 40 | **CONFIRMED, already fixed in 3.2** | Found independently by `finding/309` ~1 h earlier from the same yaml; 3.2 carries 40 N/unit everywhere |
| 4 | MAJOR — §5 hardcodes (0,1) while G0-B may drop it | **ACCEPTED** | §5 delay row now reads "(0,1) as the user-approved default, tied to `delay-range` and G0-B" |
| 5 | MAJOR — G0-B leaves [1.3×, 2×) undefined | **ACCEPTED** | Rule added: keep (0,1), mark `delay-range` marginal, let G0-C's paired probe price it |
| 6 | MAJOR — R-1 collapses to M(u)/u, assuming linearity | **CONFIRMED, already fixed in 3.2** | `finding/309`: ratio r = Δθ(0.5)/Δθ(0.25) separates linear (≈2) from quadratic (≈4), K cancels |
| 7 | MINOR — set `thrust_deadband 0.0` explicitly | **PARTLY** | Inertness is a code fact, not an assumption: `marinelab/core/thruster.py:178` returns the state unchanged when the curve is off (`finding/281`). Config stays byte-identical for attributability; G0-J now asserts `enable_thrust_curve false` (or deadband 0 if decision 9 picks option (d)) |

Tally: 2 accepted, 2 confirmed-already-fixed, 2 rejected, 1 partly. No finding touched the fault-sampler arithmetic (task A) — agy reported no deviation, which agrees with codex `review/307`.

## Gate

Two-family adversarial review: **met** for this program — codex (`review/307`, on revision 3.0) and agy (this post, on 3.1). The two families did not overlap: codex found the pair-probability arithmetic, severity integration, R-1 identifiability and the launch manifest; agy found the delay-row contradiction, the G0-B gap, and re-raised the axis question. Both independently found the 50 → 40 N constant, which `finding/309` had also found from the artifact — three readers, one number.
## Comments
