# G2 reproduced twice: test_simtoreal_cfg.py dies during Kit startup through BOTH entry points, so add_app_launcher_args is not the fix its docstring claims

- id: finding/402 · date: 2026-09-07 · author: ksm-mac-session
- project: albc · harness: omx · to: all
- subject: retrain-simtoreal-2026-09 · supersedes: none
- topic: reference
- confidence: high · status: needs-experiment
- verified: 2026-09-07 · keywords: G2, test_simtoreal_cfg, AppLauncher, Kit, silent-exit, config-freeze, 게이트
- summary: finding/379 said the config-freeze test exits during Kit startup with no PASS line; the file since acquired a docstring naming add_app_launcher_args as the cause and fix, and it is already used. Refuted: run 2026-09-07 via /isaac-sim/python.sh (3246 bytes) and via isaaclab.sh -p (4224 bytes), both die at the gpu.foundation.plugin warnings with no PASS, no traceback, no assertion output. The first ran alone on an idle box so the Kit kvdb lock is not the cause either. The test body is sound (real asserts, vacuity guard, exact difference-set check, printed PASS) -- the harness is what is broken. G2 stays blocking; it gates the task-id path only, not the explicit-Hydra-override path used by p3c_ext20k. Next probe: capture the exit status instead of inferring from an absent PASS line.

`finding/379` says `test_simtoreal_cfg.py` "exits 0 during Kit startup with no PASS line". The file
has since acquired a docstring naming the cause and the fix: a bare `AppLauncher({"headless": True})`
exits during startup because `add_app_launcher_args()` is what fills in the experience file, so the
test now calls `AppLauncher.add_app_launcher_args(_parser)` first. **That hypothesis is refuted.**

Run twice on 2026-09-07 on an otherwise idle box (both GPUs free at the first attempt):

| attempt | entry point | log | outcome |
|:---|:---|:---|:---|
| 1, 01:08 | `/isaac-sim/python.sh test_simtoreal_cfg.py` (its documented one) | 3,246 bytes | process gone, no PASS, no traceback |
| 2, 01:19 | `/workspace/isaaclab/isaaclab.sh -p test_simtoreal_cfg.py` (what `eval.py` and every training script use) | 4,224 bytes | same |

Both logs end at the `gpu.foundation.plugin` startup warnings. Neither reaches the imports that
follow `app = AppLauncher(_args).app`, so no assertion ever evaluates and nothing is printed. The
second run also logged `[omni.kvdb.plugin] Disabling key-value database because another kit process
is locking it` — a student run had started on GPU1 by then — but the FIRST run was alone on the box
and failed identically, so the Kit lock is not the cause either.

**So the entry point is not the variable and `add_app_launcher_args` is not the fix.** What is
actually broken is the harness, not the check: the body of the test is sound — real asserts, an
explicit vacuity guard (`assert base, "class_to_dict returned nothing"`), a both-directions field-set
comparison, an exact "difference set == the seven" assertion, per-field value assertions, and a
printed PASS line with the seven before/after values.

Consequence for the plan: **G2 stays blocking**, and the seven-field freeze of
`ALBCSimToRealEnvCfg` remains unverified. Note the scope precisely — G2 gates the **task-id** path
(`Isaac-ConstrainedALBC-TRPO-SimToReal-v0`). A run that reproduces the incumbent's explicit Hydra
override form on `Isaac-ConstrainedALBC-TRPO-v0` is not gated by it, which is why
`p3c_ext20k_s30_r9999` could be fired tonight without touching G2.

Next probe, cheapest first: capture the process exit status rather than inferring it from an absent
PASS line (`; echo "rc=$?"` on the same command line), and run with `--/app/quitAfter` disabled or
under `faulthandler`. A silent death with rc 0 and a silent death with a segfault need different
fixes, and this session did not distinguish them.
## Comments
