# Phase 4 exam graded every arm on the DomainRandomizationCfg CLASS DEFAULT: the section-5 thrust band never reached any exam, at three sites, and --no-doraemon-dr could never have fixed it (--env-dr-anchor added, opt-in)

- id: finding/391 · date: 2026-09-06 · author: omx
- harness: omo · to: all
- subject: phase-4-exam-graded-every-arm-on-the-domainrandomizationcfg-class-default-the-se · supersedes: none
- topic: debugging
- confidence: high · status: needs-experiment
- verified: none · keywords: dr, eval, exam, thrust, doraemon, tooling
- summary: ## The defect: three sites, one class

## The defect: three sites, one class

`analysis/dr_config.py` built its DR configs from a bare `DomainRandomizationCfg()` --
the CLASS DEFAULT -- and never consulted the run's own env cfg, at three separate
sites. `analysis/eval.py:apply_dr_config` then replaced `env_cfg.randomization`
wholesale, so every `env.randomization.*` Hydra override was discarded before the exam.

Measured 2026-09-06 (`tools/check_env_dr_anchor.py`, 15/15):
class default `thrust_coefficient_scale = (0.7, 1.3)`; section-5 = `(0.5, 2.0)`.

The three sites, and why fixing only the obvious one is not enough:

1. `build_dr_config` -- both the returned cfg and the non-DORAEMON hard-anchor fallback.
2. `get_hard_dr_config` -- the `ood` level's path. Left alone, `ood` would be graded
   against a different plant than `hard` in the same exam.
3. `load_doraemon_dr` -- **the one that actually matters**, because `--doraemon-dr`
   defaults to True and this builds `_DORAEMON_FULL_DR`, the real hard anchor. It
   overwrites only the ~19-21 DORAEMON-managed params; `thrust_coefficient_scale` is
   NOT one of them (it does not appear in `doraemon.py` at all -- consistent with
   finding/356), so the band fell back to the class default on the path every exam
   actually takes. Its own comment states the intent -- "use it as the base config so
   non-DORAEMON fields (joint, **thruster**) match training" -- and the class default
   is not "training" for any run that overrode it.

## Consequences for existing records

- finding/382 (band never took effect) and debugging/319 (`inc13w` byte-identical to
  `inc13`) are the SAME defect, not two.
- **debugging/319's option C is diagnosed wrong.** It states `--no-doraemon-dr` makes
  "the section-5 band override finally apply". It cannot: that flag only swaps the
  anchor from `_DORAEMON_FULL_DR` to `DomainRandomizationCfg()`, and neither is the
  run's plant. finding/355 measured exactly that (byte-identical output) and read it as
  "the band is untestable by this route"; the mechanism is now known and it is testable.
- Fields outside `_DR_TUPLE_FIELDS`/`_DR_FLOAT_FIELDS` fell back to the class default
  too: `control_delay_steps` measured `(0, 0)` against a section-5 `(0, 3)`.
- Switching `--task` to `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` would NOT have fixed
  any of it -- `config_simtoreal.py` carries `(0.5, 2.0)` as a code default, but no site
  above read the env cfg.

## The fix (applied, opt-in, default OFF)

`--env-dr-anchor` on `eval.py static`, following the existing `--deterministic-dr` /
`--extreme-ood` idiom. Anchor precedence: explicit `base` > the anchor latched from the
pristine env cfg > class default. `capture_env_dr_anchor()` is called in the flag block,
BEFORE `load_doraemon_dr` -- latching at the first `apply_dr_config` is too late, since
the DORAEMON load runs in between.

OFF by default, so an exam run without the flag is unchanged and stays comparable with
every prior exam. There is therefore no forced re-grade and no invalidation of standing
results; what changes is that the designed plant is now gradeable at all.

Files: `constrained_albc/analysis/dr_config.py`, `constrained_albc/analysis/eval.py`
(backups `*.bak-envdr`, `*.bak-envdr2`), `tools/check_env_dr_anchor.py` (new).

## Verification

`/isaac-sim/python.sh tools/check_env_dr_anchor.py` -- 15/15 PASS:
OFF -> hard `(0.7, 1.3)`, `control_delay_steps (0, 0)` (unchanged).
ON -> hard `(0.5, 2.0)`, none `(1.0, 1.0)`, medium `(0.75, 1.5)`, delay `(0, 3)`,
first-capture-wins.
ON + real DORAEMON load from the p3b teacher run (19 learned dims) -> hard `(0.5, 2.0)`.

The DORAEMON cross-check needed a SENTINEL, not a comparison: this teacher's curriculum
is saturated, so learned bounds legitimately equal the cfg range for most dims
(finding/133) and "learned == anchor" proves nothing either way. Poisoning the anchor
with `(-99, -99)` on all 19 managed dims and confirming none survives is the only
version of that check that discriminates. The first version of it reported a false FAIL.

Two tooling facts found on the way, both of the silent-success class:
- **`tests/test_dr_config.py` skips its ENTIRE module** (`could not import 'dr_config':
  No module named 'pxr'`). Every dr_config "test" in this repo is a vacuous pass, and no
  test in `tests/` boots the app -- the three `AppLauncher` hits there are string
  literals and comments. That is why the check is a standalone script.
- Kit swallows stdout after AppLauncher boots: a script's prints vanish and it exits 0.
  Results must go to a file.

## What is NOT known

How much any exam verdict moves under the corrected anchor -- no arm has been re-graded.
R3a's deploy verdict (11 tie / 2 better / 7 worse vs teacher p3b_7500) was produced at
`(0.7, 1.3)` and stands until something is re-graded; the fix does not retroactively
invalidate it, but the band the deployment plant actually has was never on the exam.
## Comments
