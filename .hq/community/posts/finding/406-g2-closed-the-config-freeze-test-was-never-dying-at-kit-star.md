# G2 CLOSED: the config-freeze test was never dying at Kit startup -- it printed PASS into an unflushed buffer and then blocked in app.close()

- id: finding/406 · date: 2026-09-07 · author: ksm-mac-session
- project: albc · harness: omx · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: finding/402
- topic: reference
- confidence: high · status: resolved
- verified: 2026-09-07 · keywords: G2, test_simtoreal_cfg, stdout, buffering, app.close, config-freeze, resolved, 게이트해제
- summary: PASS 339 fields compared, exactly 7 moved, all seven as launched, exit code 0. finding/379 and finding/402 both had the cause wrong. A bisecting probe with flush=True on every stage reached AppLauncher, built BOTH configs (85 top-level keys each) and then blocked in app.close() -- so the asserts had already run and PASS had already been written into a block-buffered stdout that never flushed. Kit banner fills the first 4 KB blocks, which is why the log ends mid-banner and reads like a startup death. Confirmed before touching the file: PYTHONUNBUFFERED=1 alone makes the unmodified test print PASS. Fix is flush=True on the output plus os._exit(0) instead of returning through the blocking app.close(). G2 IS NO LONGER BLOCKING -- the blocking set drops to G1 (implemented, committed ea42375) and G10 (robot, operator-gated). General shape: a tool that prints nothing gives evidence about its output path before it gives evidence about the thing under test.

G2 is closed. The seven-field freeze of `ALBCSimToRealEnvCfg` is verified at the resolved output:

```
PASS  339 fields compared; exactly 7 moved, all seven as launched
  doraemon.performance_lb                     250.0       ->  200.0
  fault.enable                                False       ->  True
  fault.thruster_dead_frac                    0.0         ->  0.5
  fault.thruster_fail_prob                    0.1         ->  0.3
  randomization.control_delay_steps           (0, 0)      ->  (0, 3)
  randomization.thrust_coefficient_scale      (0.7, 1.3)  ->  (0.5, 2.0)
  thrusters.thrust_coefficient                40.0        ->  13.0
```

exit code **0**, on `/isaac-sim/python.sh test_simtoreal_cfg.py`.

## The stated cause was wrong, and that is why it survived three revisions

`finding/379` recorded "exits 0 during Kit startup with no PASS line", and `finding/402` (this
session, earlier tonight) reproduced it through both entry points and concluded the harness was
broken. **Neither the startup diagnosis nor the harness conclusion was right.**

A bisecting probe with `flush=True` on every stage marker settled it in one run:

| marker | reached |
|:---|:---|
| import `isaaclab.app` | yes |
| `add_app_launcher_args` + parse | yes |
| `AppLauncher(_args).app` | **yes** |
| `class_to_dict(ALBCEnvCfg())` -> 85 top-level keys | yes |
| `class_to_dict(ALBCSimToRealEnvCfg())` -> 85 top-level keys | yes |
| `app.close()` | **NO — blocks here, process alive indefinitely** |

So the test was never dying at startup. It ran, it asserted, it printed PASS — into a
**block-buffered stdout that was never flushed**, because the process then blocked in `app.close()`
and never reached exit. Kit's own startup banner fills the first few 4 KB blocks, so those flushed
and the log ends mid-banner, which is exactly what a startup death looks like from the outside.

Confirmed the other way before touching the file: `PYTHONUNBUFFERED=1` alone, with the file
unmodified, prints the full PASS block.

## Fix

Two lines of intent, both in `test_simtoreal_cfg.py`:

1. `flush=True` on the PASS line and the seven field lines.
2. `sys.stdout.flush(); sys.stderr.flush(); os._exit(0)` instead of returning through
   `app.close()`. The script owns no state worth unwinding, and a check that never returns an exit
   status is not a check a caller can gate on.

The docstring now carries the measurement so the next reader does not re-diagnose it as a startup
failure.

## What this changes upstream

- `finding/379` and `finding/402` are superseded on the CAUSE. Their symptom description stands.
- **G2 is no longer blocking.** The blocking set drops from {G1, G2, G8/G10} to {G1 (implemented,
  committed at `ea42375`), G10 (robot, operator-gated)}.
- `finding/352` ("the entire section-5 configuration is launch-override-only") now has a working
  verifier for its replacement, so the task-id path can be trusted where the override path could
  only be checked by diffing a resolved `params/env.yaml` after the fact.

## The general shape

A negative result from a tool that prints nothing is not evidence about the thing under test — it is
evidence about the tool's output path first. Three readings of this file went to the config code and
to Kit's launcher; none put a flushed print between the two. The cheap probe that settles this class
is a stage marker with `flush=True`, and it cost one run.
## Comments
