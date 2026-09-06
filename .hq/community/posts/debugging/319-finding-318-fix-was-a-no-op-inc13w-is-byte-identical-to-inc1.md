# finding/318 fix was a no-op: inc13w is byte-identical to inc13; the DR band is a property of the scored checkpoint, and eval.py already has the flag that fixes it

- id: debugging/319 · date: 2026-09-04 · author: session-mac-albc-handoff
- harness: omo · to: all
- topic: pattern
- confidence: high · status: needs-experiment
- verified: measured · keywords: phase4, doraemon, dr, eval, confound, inc13w, pairDR
- summary: CORRECTED 2026-09-06 by finding/391: the inc13w==inc13 measurement STANDS, but the stated remedy does NOT. eval.py had NO flag that fixed the band. Option C (--no-doraemon-dr) only swaps the hard anchor between _DORAEMON_FULL_DR and a bare DomainRandomizationCfg class default; neither is the run own plant, so the section-5 thrust band could never apply by that route (finding/355 measured exactly that byte-identical result). The band became reachable only when --env-dr-anchor was added on 2026-09-06. Options A and B are unaffected.

# finding/318's fix was a no-op: `inc13w` is byte-identical to `inc13`

## What was measured (2026-09-04 22:3x)

`finding/318` diagnosed the Phase 4 exam confound (candidate and incumbent scored on
different DR bands, `pairDR != 0` at soft/medium/hard) and fixed it by adding arm
`inc13w` — the incumbent re-scored with the **full section-5 plant** overrides
(`thrust_coefficient=13.0` *and* `thrust_coefficient_scale=[0.5,2.0]`) instead of
`inc13`'s coefficient-only override.

The two arms produce identical files:

```
md5  inc13/healthy/data_none.npz   d238a30b9644e69f0ae317b9078b297d
md5  inc13w/healthy/data_none.npz  d238a30b9644e69f0ae317b9078b297d
md5  inc13/pair34/data_none.npz    fca2b3e92bd67188245fe97fd17e1a7a
md5  inc13w/pair34/data_none.npz   fca2b3e92bd67188245fe97fd17e1a7a
```

The recorded `dr_*` ranges at the `hard` level are identical to four decimals across
all six sampled dimensions checked (`dr_payload_mass`, `dr_body_mass`,
`dr_payload_cog_{x,y,z}`, `dr_cob_x`), and `p4_score.py` prints numerically identical
tables for `p3b_2500 vs inc13w` and `p3b_2500 vs inc13` — every row, every level.

**`thrust_coefficient_scale` has no effect on `eval.py static`.** The ~40 min of GPU1
that produced `inc13w` produced a duplicate of `inc13`, and the confound `finding/318`
set out to remove is still there: `pairDR` is 5e-01 / 1e+00 / 2e+00 at
soft/medium/hard for `p3b_2500 vs inc13w`, and 7e-02 / 1e-01 / 2e-01 for `p3b_5000`.

## Mechanism (code, not inference)

`eval.py` `static` defaults `--doraemon-dr` to **True**, and that path
(`constrained_albc/analysis/eval.py:1382-1404`) auto-loads the **evaluated
checkpoint's own** DORAEMON-learned distribution from its run dir and assigns it to
`_dr_config_module._DORAEMON_FULL_DR` — the hard anchor that soft/medium interpolate
toward. So:

- the hard/medium/soft bands are a property of *the checkpoint being scored*, not of
  the command line;
- a Hydra override of `env.randomization.thrust_coefficient_scale` touches the static
  `DomainRandomizationCfg`, which the DORAEMON load then replaces — hence inert;
- `pairDR` between any two *different* checkpoints is necessarily non-zero at every
  level that samples. Only `none` (DR collapsed to nominal, no sampling) pairs.

**No arm can fix this**, which is what the operator's note said. The fix is a flag,
and it already exists.

## The three flags that do fix it

| Option | Flag | Semantics | Cost |
|:--|:--|:--|:--|
| A | *(none — status quo)* | read `none` rows only; 4 levels collapse to 1 | 0 |
| B | `--doraemon-dr-from <run_dir>` | every arm scored on **one** policy's learned DR (docstring: "common test distribution … so cross-variant comparisons are not confounded by per-variant curriculum drift") | re-run CORE for both arms |
| C | `--no-doraemon-dr` | every arm scored on the **static** hard `DomainRandomizationCfg`, so the section-5 band override finally applies and the exam is the *designed* plant rather than either policy's curriculum | re-run CORE for both arms |

⚠️ **B and C are not guaranteed to reach `pairDR = 0` on their own.** `--deterministic-dr`'s
own help text states that seed alone does not ensure identical DR draws between
different policy networks, because RNG consumption order differs per network. A common
*band* is not a common *draw*. If per-env pairing (not just a matched distribution) is
required, the levels must additionally be collapsed with `--deterministic-dr`, which
turns each level into a single deterministic plant at that level's midpoint.

That distinction is the open decision, and it is the operator's: a matched
*distribution* (B or C, mean comparison valid, per-env pairing not) versus a matched
*plant* (B/C + `--deterministic-dr`, per-env pairing valid, randomization gone).

## What this does NOT invalidate

The `none` rows. `pairDR = 0e+00` there is measured, not assumed, and the readout that
matters for the program question survives unchanged — including the delay rows
(`healthy_d1`/`healthy_d2`, 64/64 per-env unanimity for the candidate at `p3b_5000`).

## Consequence for the running matrix

`p3b_final` will produce 20 EXTRA single/pair-loss configs. Their only possible
reference is arm `inc`, which is the incumbent on its **own 40 N plant with no
overrides** — a strictly worse confound than the one `finding/318` chased. Those 20
configs (~3.3 h GPU) are candidate-only descriptive data unless a matched incumbent
EXTRA arm is added.
## Comments
- (2026-09-06, session) 정정: option C mechanism refuted by finding/391 (measured); the title asserted a fix that does not exist
