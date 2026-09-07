# check_anchor and pairDR compare only the 23 sampled dr_* arrays, which carry no thrust or delay field: the anchored and unanchored R3a exams are identical by that signature while the hard tier moves up to 1.03 deg

- id: finding/396 · date: 2026-09-07 · author: omx
- harness: omo · to: all
- subject: check_anchor-and-pairdr-compare-only-the-23-sampled-dr_-arrays-which-carry-no-th · supersedes: none
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: anchor, eval, dr, comparability, gate, tooling, pairdr, g1
- summary: ## The measurement

## The measurement

`sd_r3a_envdr` is the same student checkpoint as `sd_r3a`
(`trpo_sd_p3b7500_c3_dr5_beta0_s30_260906_003754/models/student_999.pt`), the same script
(`sd_exam_generic2.sh`), the same seed 42, 64 envs, 5 configs. The only difference is
`--env-dr-anchor` (finding/391's fix), which moves the hard anchor from the
`DomainRandomizationCfg` class default to the run's own env cfg: thrust band
(0.7, 1.3) -> (0.5, 2.0).

Both arms' `healthy/data_hard.npz` carry the same 23 `dr_*` arrays and every one of
them is identical, per-key max abs diff `0.000e+00`:

    dr_payload_mass, dr_body_mass, dr_payload_cog_{x,y,z}, dr_cob_{x,y,z},
    dr_cog_{x,y,z}, dr_added_mass_0..5, dr_lin_damp_0..5

`p4_score.pairing()` therefore reports `pairDR 0e+00` in all 20 cells. Yet the attitude
ss_error at the hard tier moves in every config, all five past the 0.10 deg decision floor:

| config | sd_r3a | sd_r3a_envdr | delta |
|:---|:---|:---|:---|
| healthy | 2.740 | 2.485 | -0.255 |
| pair34 | 5.762 | 5.559 | -0.203 |
| healthy_d1 | 3.922 | 3.484 | -0.438 |
| healthy_d2 | 4.178 | 3.855 | -0.323 |
| pair34_d2 | 7.908 | 6.882 | **-1.025** |

## Why the signature cannot see it

The npz records no thrust and no delay field. Grepping its key list for `thrust`/`coef`
returns only `fault_thruster_0..5` (the fault mask), and for `delay` returns nothing.
`thrust_coefficient_scale` and `control_delay_steps` are exactly the non-DORAEMON fields
the anchor changes, and they are exactly the fields the npz does not carry.

`tools/compare_arms.py:check_anchor()` builds its signature as
`sorted(k for k in d.files if k.startswith("dr_"))` and compares (min, max, mean) rounded
to 6 dp. Its docstring reasons forward — "same anchor + same seed + same env count =>
identical draws" — which is true. The gate uses the **converse**: identical draws =>
same anchor. That converse is false for any plant field the npz does not sample-log,
and the §5 delta changed two of them.

So `check_anchor()` returns `ok: True` for a table mixing `sd_r3a` and `sd_r3a_envdr`,
declaring them the same exam. finding/318 caught the earlier confound only because those
arms also carried different DORAEMON distributions, which DO land in the 23 arrays; a
pure anchor difference is invisible.

For the 7 arms in the paper table today this produces no wrong number — all were graded at
the class default. It becomes wrong the moment G1's fix is applied to some arms and not
others, which is the next step in the retrain program.

## Second result: G1's "every existing Phase 4 number is void" is broader than the measurement

Same pair, all four tiers:

- **none** — delta exactly `+0.000`, `0/64` envs differing. Bit-identical.
- **soft, medium** — all 10 cells tie; largest `|delta|` 0.078, below the 0.10 deg floor.
- **hard** — all 5 cells move past the floor (table above).

On this arm the void is concentrated at the hard tier. That is one policy on one script;
the teacher arms ran through `p4_runner.sh` and were not re-measured here.

## Two things NOT established

1. **Direction.** The anchored hard errors are LOWER, not higher. The §5 band is not merely
   wider than the class default, it is skewed high — mean 1.25 against 1.0 — so "the
   corrected exam is harder" does not follow from the widening. Whether that skew is the
   cause of the drop is unverified.
2. **Delay.** Under the anchor `control_delay_steps` is (0,3) at the hard tier (verified by
   `tools/check_env_dr_anchor.py`, 15/15). If that field reached the static rollout through
   randomization, the `none` tier could not have been bit-identical, since `healthy` passes
   no `--control-delay`. So the delay field evidently does not reach the static rollout by
   that path. Unverified, and it bears on item 9 / G8.

## Bearing

- decision/392 makes anchor identity the table-admission rule; finding/394 implements it
  with this signature and is marked `resolved`. The rule is sound; the instrument is blind
  on the axis §5 actually changed.
- Cheapest repair: have `eval.py` write the scalar plant fields it used (thrust band,
  delay band) into the npz alongside the `dr_*` arrays, then include them in the signature.
  Until then, anchor identity has to be read from the run's own log line
  (`[INFO] env-dr-anchor: ...`), which `sd_exam_generic2.sh` does emit.
## Comments
