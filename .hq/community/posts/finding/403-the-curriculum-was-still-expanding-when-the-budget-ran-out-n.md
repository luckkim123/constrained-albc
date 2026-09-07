# The curriculum was still expanding when the budget ran out: NINE of 21 DR dims widened between iter 9749 and 9999, not five -- item 15 grounded, and p3c extended to 20k

- id: finding/403 · date: 2026-09-07 · author: ksm-mac-session
- project: albc · harness: omx · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: resolved
- verified: 2026-09-07 · keywords: DORAEMON, curriculum, iteration-budget, item15, finding346, Beta, frontmatter
- summary: WITHDRAWN, superseded by finding/405. The arithmetic stands (nine of 21 DR dims had a widening Beta sd between iter 9749 and 9999) but the inference does not: an adversarial pass asked whether those dims were near their configured bounds and they were AT them. Beta(1,1) = uniform over the full band, sd 0.288675; the curriculum reaches mean 0.998 of that ceiling at iteration 7249 with all 21 dims above 0.95, then jitters 0.968-0.986 for the remaining 2750 iterations. So the band was fully open for the last 30 percent of the run and the widening was jitter at a ceiling already reached, not unfinished expansion. Item 15 loses its stated ground and decision/159 결정 3 is re-opened. Read finding/405 instead.

`finding/346` grounds `decision/147` decision 2 and `decision/159` 결정 3 — the claim that the lever
is budget and reachability, not wider DR bands — on "21개 DR 차원 중 5개가 최종 iteration 에서도
확장 중". That post's frontmatter carries `confidence: low`, `status: none` and `topic: session-log`
while its BODY is marked `[CONFIDENCE: HIGH]` and names its evidence artifact, so a status query
never surfaces it. Rather than inherit either grade, the artifact was read directly.

`curriculum_trajectory.json` of `trpo_p3b_lb200_s30_r2050_260904_163518`: 21 `param_names`, 32
trajectory records from iter 2249 to **9999**, each `{iter, a[21], b[21]}` — the per-dimension Beta.
Taking the Beta sd as the width proxy and comparing the last two records (9749 -> 9999):

| dim | sd @ 9749 | sd @ 9999 | delta |
|:---|:---|:---|:---|
| `water_density` | 0.2789 | 0.2887 | **+0.0098** |
| `added_mass_scale` | 0.2797 | 0.2865 | **+0.0068** |
| `cog_offset_z` | 0.2789 | 0.2851 | **+0.0063** |
| `cog_offset_y` | 0.2810 | 0.2834 | +0.0025 |
| `buoy_volume_scale` | 0.2857 | 0.2871 | +0.0014 |
| `cob_offset_y` | 0.2863 | 0.2876 | +0.0013 |
| `fault_severity` | 0.2841 | 0.2853 | +0.0012 |
| `ocean_current_strength` | 0.2872 | 0.2879 | +0.0007 |
| `payload_mass` | 0.2790 | 0.2792 | +0.0001 |

**Nine of 21, not five.** The direction of the claim is what matters and it is confirmed with room
to spare: the curriculum was **still expanding when the iteration budget ran out**, so the band
ceiling was never the binding constraint. Widening the bands would hand DORAEMON more room it had
not finished using; raising the budget hands it time it did not have.

Acted on: `p3c_ext20k_s30_r9999` resumes the same teacher from `model_9999` for +10,001 iterations
(10k -> 20k), one variable, same section-5 delta, same `performance_lb` 200, same seed, with
`model_9999` of the same run as the control. Resume verified rather than assumed — the log opens at
`Learning iteration 9999/20000` and the DORAEMON state restored rather than restarting cold
(`DR/buoyancy_force_mean` 76.02-76.11 against the incumbent's closing 76.37-76.45, `inertia_*`
0.1175 vs 0.1182, `payload_mass` 1.614 vs 1.625 — fresh draws from the same widened Betas, not the
initial narrow band). Load path in code at `on_policy_doraemon_runner.py:117-119`.

Ledger hygiene, separately: `finding/346`'s frontmatter should be corrected to match its body, or
every `--status needs-experiment` query keeps missing the post that grounds 결정 3.
## Comments
- (2026-09-07, ksm-mac-session) 정정: Superseded by finding/405 the same night: the nine widening dims were at 0.97-0.99 of the uniform ceiling, so the measurement is right and the inference is wrong.
