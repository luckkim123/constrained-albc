# R2 — bug fixes, the GRU student change, tests

Reviewer 2 of 2. Scope: WP2 (3ebe129), WP11 (a964d89), _REPO_ROOT (73eb827), WP10a
(c1677c3), segmented refusal (e4ba44c), test deletion (ff47492), and every change under
`tests/`. Read-only; no file on the container was modified.

## (A) Verdict table

| Commit | Verdict | Reason |
|:---|:---|:---|
| 3ebe129 WP2 (six eval/deploy defects) | **NEEDS-FIX** | D8 (undeclared in the subject) turns `_read_manifest_if_present` into a raiser, so one corrupt manifest now aborts every `find_runs` scan instead of skipping that run |
| a964d89 WP11 (GRU hidden reset) | **MERGE-SAFE** | Per-env/per-step zeroing is mathematically correct and matches the buffer's `(envs, T)` `prev_dones` layout; two caveats below are notes, not blockers |
| 73eb827 `_REPO_ROOT` hop fix | **MERGE-SAFE** | Three hops is right for the new depth; the defect was created and closed inside this branch, so net effect on main is zero |
| c1677c3 WP10a (style/deploy docs) | **MERGE-SAFE** | Purely mechanical; the single non-cosmetic hunk is a Yoda-condition reorder in a test assertion |
| e4ba44c segmented refusal | **NEEDS-FIX** | The code is correct, but it collides head-on with the p5 branch in three hunks and, as written, makes `eval.py segmented` raise for every registered task |
| ff47492 test deletion | **MERGE-SAFE** | The deleted test asserted on its own arithmetic and its production counterpart no longer exists |
| WP0 test unpinning (part of 0001) | **MERGE-SAFE, one weakening** | Five hardcoded-path tests now resolve from `__file__`; `test_cli_emits_json` gained a `pytest.skip` |
| a117db3 test file swap (under tests/) | **MERGE-SAFE** | `test_marine_feature_obs.py` (3 tests) deleted with the Koopman feature; `test_obs_cfg_surface.py` (2 tests) replaces it with a frozen-surface gate |

## (B) Findings by severity

### F1 (HIGH) — a corrupt manifest now crashes every run scan, and it is not in the commit's own list

`3ebe129` changed `constrained_albc/analysis/paths.py::_read_manifest_if_present` from
returning `None` on `json.JSONDecodeError`/`OSError` to raising `RuntimeError`. Its only
in-module caller is `_is_run_dir`, which `find_runs` calls once per candidate directory
under the experiments root.

Failure scenario. `train.py` is killed while `write_manifest` is mid-write, leaving one
truncated `manifest.json`. Before: `find_runs` skips that directory and returns every other
run. After: `find_runs` raises on it, so `resolve_run`, `list_runs`, `monitor.py`,
`_encoder/debug.py` and `.hq/config/experiments/profile/analyze_training.py` all die with
an exception naming a run the caller never asked for. A single interrupted training run
disables run resolution for the whole tree.

The fix is one line at the scan boundary: let `_is_run_dir` catch and warn, keeping the
raise for direct callers who named the run. The commit's own test only asserts the raise
from `_read_manifest_if_present` directly and never exercises `find_runs` over a corrupt
directory, so this path is untested in both directions.

Ledger note attached to the same finding: the commit subject and body enumerate D2, D3, D4,
D5, D6, D7. D8 appears nowhere in the message, only in a test comment and in the CHANGELOG.
The CHANGELOG in turn enumerates D2, D4, D5, D6, D8 and omits D3 and D7. Both documents say
"six"; the union is seven.

### F2 (HIGH) — the segmented refusal makes the mode unreachable, and collides with p5

At the cleanup tip, `_vel_cmd_lin` is defined by no environment at all. I enumerated every
tracked `.py` at `ff47492`: the only remaining mentions are in `analysis/eval.py`,
`analysis/_eval_dr/metrics.py`, two test files, and two comment lines in
`envs/tdc_main/tdc_env.py` that say the attribute does **not** exist there. So the new
`if not hasattr(raw_env, "_vel_cmd_lin"): raise RuntimeError(...)` fires for every
registered task and `eval.py segmented` becomes a mode that can only fail.

That is arguably the honest state, because the same is true at the base commit: at
`98dd2f2`, `envs/main/albc_env.py` contains zero occurrences of `_vel_cmd_lin` and
`run_switching_eval` wrote it unguarded, so segmented already raised `AttributeError` on
every main task. The cleanup does not remove a working capability; it replaces an
accidental crash with a diagnosed one. But it should be stated in the merge decision that
segmented has no surviving user, rather than left implicit.

The collision is real and mechanical. `CONFLICT_eval.py` is not a branch snapshot, it is an
attempted-merge artifact carrying live conflict markers at three sites:

| Lines | Region | p5 side | cleanup side |
|:---|:---|:---|:---|
| 1905-1923 | `run_robustness_eval` setup | latches a yaw heading, writes `_vel_cmd_lin[:] = 0.0` unguarded | zeroes `_ang_cmd[:]`, guards the `_vel_cmd_lin` write with `hasattr` |
| 1936-1947 | `run_robustness_eval` step loop | re-asserts the latched heading, unguarded write | same guard |
| 2321-2329 | `run_switching_eval` command block | `_ang_cmd[:, 2] = 0.0` heading, no yaw P-loop | unguarded `_vel_cmd_lin` writes |

### F3 (MEDIUM) — two tests still import the live `/workspace/marinelab`

The unpinning claim holds for `constrained_albc` and for the file-path-based marinelab
tests, and I verified the mechanism rather than trusting the pass count. The editable
install's finder installs itself with `sys.meta_path.append`, so the standard `PathFinder`
still runs first; under `python -m pytest` the worktree root is `sys.path[0]` and its
`constrained_albc/` package wins over `/workspace/constrained-albc`. The 510-pass run did
test the worktree.

`marinelab` is different. The worktree root has no `marinelab/` directory, so `PathFinder`
misses and `_EditableFinder` resolves `marinelab` to `/workspace/marinelab` — the live
p5 checkout. Two tests import it by name rather than by path:
`tests/test_buoy_dr.py` and `tests/test_current_migration.py`. The four file-path tests
(`test_doraemon`, `test_fault_dr`, `test_fault_fixed_health`, `test_max_thrust_identity`)
correctly resolve `parents[2] / "marinelab"`, i.e. the ponytail sibling. This is not
fixable inside the test and both import-based tests skip without Isaac Sim, but the
CHANGELOG sentence "in any clone they exercised the canonical repos" is only fully closed
for the path-based ones.

### F4 (LOW) — `test_cli_emits_json` was converted to a conditional skip

`tests/test_eval_adapter.py::test_cli_emits_json` gained
`pytest.skip("fixture absent — copy from SOURCE.txt")` in WP0. `tests/fixtures/eval/`
contains only `SOURCE.txt` on disk and `.gitignore` excludes `tests/fixtures/*` except
`encoder/`, so the fixture is never present in a fresh clone and this assertion is now
permanently inert there. Defensible (the alternative is a permanent red), but it is a
weakening and the commit message does not call it out.

### F5 (LOW) — "bit-for-bit unchanged" is precise only when no env resets

In `_gru_seq_forward`, an all-clean window takes the whole-batch fused call and is
genuinely identical. In a mixed window, clean envs take
`self.student(x_seq[clean], hidden=h_in[:, clean])` — a fused call over a **smaller batch**.
That is mathematically identical but not bitwise guaranteed under cuDNN, where batch size
can select a different kernel. The regression test asserts `torch.equal` on the clean
siblings, but on CPU float64, so nothing will surface in CI.

### F6 (LOW) — two latent traps in `_gru_seq_forward`

`out = x_seq.new_zeros(..., o_dirty.shape[-1])` takes its dtype from the input, not from
the encoder output. Under autocast, or any future mixed-precision distillation, `o_dirty`
would be half while `out` is float and `index_copy` raises. Second: the dirty branch runs
one GRU call per timestep, so a 24-step window costs 24 sequential launches per minibatch
per epoch. Early in training, when terminations are frequent and most envs are dirty, this
is a real slowdown of the distillation stage. Neither is a correctness defect.

### F7 (LOW) — `_run_recency_key` can raise on a timezone-aware `created`

`datetime.fromisoformat` accepts an offset suffix and returns an aware datetime; the
fallback `_parse_run_ts` and the `datetime.min` default are naive. A tree mixing one
manifest carrying an offset with any legacy run lacking a manifest makes `runs.sort` raise
`TypeError: can't compare offset-naive and offset-aware datetimes`. Today's writer is
`datetime.now().isoformat(timespec="seconds")`, which is naive, so this only bites a
hand-written or foreign manifest.

## (C) Answers

### 1. WP11 — old vs new behaviour, correctness, test discrimination, DAgger alignment

**Old.** In `learn`, before the epoch loop:
`any_done_in_rollout = self.buffer.done_flat[:T_].any(dim=0)`, then
`h_start = self.train_hidden.detach().clone()` and `h_start[:, any_done_in_rollout] = 0.0`.
`_compute_loss_gru` ran a single fused `self.student(x_seq, hidden=h_in)` over the whole
window, and the end-of-rollout recompute applied the mirror-image collapse,
`h_end[:, any_done_in_rollout] = 0.0`.

**New.** `h_start` is the raw carried hidden, and both call sites route through
`_gru_seq_forward`, which zeroes the hidden fed **into** step *t* whenever
`dones_seq[e, t]` is true.

**Is it right?** Yes. I verified the alignment rather than taking the docstring's word for
it. In `collector.py`, `done_flat` has shape `(n_steps, num_envs)`, is written at
`done_flat[self.step_idx] = dones` in the same `add` call that stores `obs_t`, and the GRU
minibatch emits `dones_seq = done_flat[:T, idx].transpose(0, 1)` right beside
`obs_seq = obs_flat[:T, idx].transpose(0, 1)`, both `(envs, T)`. So `dones_seq[e, t]` marks
`obs_t` as the first observation of a new episode, and zeroing the hidden before consuming
`obs_t` is exactly the reset the collector performs. `learn`'s recompute passes
`done_flat[:T_].transpose(0, 1)`, the same layout. The mask is applied as
`hd * (~dd[:, t]).view(1, -1, 1)`, which broadcasts across GRU layers, so multi-layer is
handled. Dropping `h_end[:, any_done] = 0` is sound because a reset at the rollout boundary
reappears as the next rollout's `dones_seq[:, 0]`.

**Is "bit-for-bit unchanged" true from the code?** Only in the all-clean case, where the
function short-circuits to the original fused call. See F5.

**Does the new test discriminate?** Partly. `test_hidden_resets_at_the_done_step` contains
an explicit anti-collapse assertion (`assert not torch.allclose(got[0, :k], collapsed[0, :k])`),
so it does distinguish the fixed function from the `any()` collapse. But it binds
`StudentRunner._gru_seq_forward` directly, and that function does not exist on the pre-fix
code, so against real pre-fix `runner.py` the test errors with `AttributeError` rather than
failing on the math. The commit's "watched FAILING" claim refers to a hand-reverted copy of
the function, which is a manual observation the suite cannot reproduce. The integration is
also unguarded: nothing asserts that `_compute_loss_gru` passes `batch.dones_seq` at all.
Passing `None` there would restore the old fused behaviour and every test would still pass.
The AST gate in `test_student_extra_parity` would catch a revert that calls
`self.student` directly from `_compute_loss_gru`, but not a `None` argument.

**DAgger loss alignment.** Unaffected. `_gru_seq_forward` returns an output shaped
`(envs, T, latent)` reassembled into the original env order by `index_copy` along dim 0, so
the downstream `reshape(M, -1)` pairs the same prediction with the same target as before.
What changes is only which hidden produced each step's prediction.

### 2. WP2 — the six defects

| Defect | Fix correct? | Test exercises the path? |
|:---|:---|:---|
| D2 run-log pointer glob | Yes — `.hq/work/experiments/runs` replaces the retired `.omx/runs` | **No test.** A shell script with no gate; the fix rests on the author's "verified present" |
| D3 legacy scan depth | Yes — `root.glob("*/*")` plus `root.glob("*/*/*")` covers both layouts | Yes — `test_legacy_scan_reaches_the_group_layer` builds a real `<exp>/<group>/<run>` tree with a tfevents file and asserts the hit |
| D4 newest-by-time | Yes — sorts on manifest `created`, falls back to the run_id timestamp; the shared `_parse_run_ts` removes the duplicate parser | Yes — two tests, one per branch of the key. See F7 for the aware/naive edge |
| D5 `--spec` rejects `--golden`/`--report` | Yes — both are top-level `store_true` flags, so `getattr` is safe, and the raise precedes `resolve_out_dir` | Yes — parametrized over both flags, calls `main()` and asserts the flag name is in the message |
| D6 symlink failure | Yes — logs the failure and points the manifest at the log dir | **No test** |
| D7 eval summary traceback | Yes — keeps the swallow, prints type and stack | **No test**, and none is practical: `eval.py` boots Isaac Sim at import |
| D8 corrupt manifest raises | Correct in isolation, wrong at the scan boundary | Test asserts the raise directly, never through `find_runs`. See F1 |

**Effect on the p5 chain's pack stage.** None. `scripts/export_deploy_pack.py` imports only
`constrained_albc.deploy.__main__.main`, and `--batch attitude_only_5000` is handled in a
branch that returns before the `if args.spec:` block where D5's rejection lives. The pack
path never calls `resolve_run`, `find_runs` or `emit_run_manifest` — those callers are
`analysis/common.py`, `analysis/monitor.py`, `analysis/_encoder/debug.py` and the profile's
`analyze_training.py`. So D3, D4, D6 and D8 cannot move the pack, and D2 and D7 are in a
shell script and an eval-only branch. The pack stage is untouched by all six.

### 3. `_REPO_ROOT` hop count

Correct. The file is at `constrained_albc/algorithms/student/config.py`, so
`dirname(__file__)` is `<repo>/constrained_albc/algorithms/student` and three `..` hops
reach `<repo>`. Four hops reached the directory **above** the repo, which on this container
is `/root/orca/workspaces/workspace/ponytail` — the worktree parent. Every student run
before the fix wrote `logs/rsl_rl/...` and `experiments/rsl_rl/...` there.

Worth stating for the merge decision: this defect was **introduced by WP4 inside this same
branch** (the module moved from `constrained_albc/envs/_core/student/`, depth 4, where four
hops was right) and closed nine commits later. Net effect on `main` is zero. The guard
(`tests/test_student_log_root.py`, 2 tests) is a genuine gate: it asserts `_REPO_ROOT ==
REPO` and that `log_dir_root` is relative to the repo, and both fail on the unfixed module.

### 4. e4ba44c vs the p5 segmented rewrite

**What old segmented did.** `run_segmented` built the env, then `run_switching_eval` ran a
cascade position loop: velocity command from position error into `_vel_cmd_lin`, and a yaw
**rate** command from `kp_yaw * yaw_err` clipped at `yaw_rate_sat` into `_ang_cmd[:, 2]`.
Both npz-logged as `vel_cmd_*` and `yaw_rate_cmd`.

**What the refusal breaks.** Nothing that currently works, because nothing currently works.
No environment at `ff47492` defines `_vel_cmd_lin`, and none did at `98dd2f2` either, so
the mode raised `AttributeError` at base and raises `RuntimeError` with a diagnosis now. I
did not find a script or exam config invoking `segmented`; that search is listed in section
D as incomplete, so treat it as unconfirmed rather than proven absent.

**Proposed resolution: keep both, p5's semantics wins the yaw slot.**

1. Take the p5 side wholesale in the `run_switching_eval` hunk (line 2321): the heading
   target is a live plant change matching the running training, and the yaw P-loop is gone
   for a reason. Discard the cleanup's unguarded `_vel_cmd_lin` writes as a separate
   question, resolved by point 3.
2. Take the p5 side for the yaw halves of both `run_robustness_eval` hunks (1905, 1936) —
   the latched-heading logic — but **keep the cleanup's `hasattr` guard** on the
   `_vel_cmd_lin` writes in both. This is not a stylistic preference: on the p5 branch those
   writes are unguarded and no environment has the attribute, so `eval.py robustness` raises
   `AttributeError` there today. The cleanup's guard is the only thing making that mode run,
   and it publishes nothing false because the path records no command.
3. Keep the cleanup's `run_segmented` setup refusal verbatim, and keep
   `run_switching_eval`'s writes unguarded beneath it. The refusal is what licenses the
   unguarded writes, and together they turn a mode that fails obscurely into one that fails
   with its cause named. Both new tests in
   `tests/test_eval_segmented_lin_vel_gate.py` survive this resolution unchanged, since one
   asserts a `hasattr` plus a `raise` inside `run_segmented` and the other asserts the
   absence of `hasattr` inside `run_switching_eval`.

The merged file must then be re-checked against the p5 `--kp_yaw`/`--yaw_rate_sat`
deprecation warning, which sits in the same function and is not in a conflict hunk.

### 5. Test integrity

`def test_` counts, base `98dd2f2` versus tip `ff47492`, changed files only:

| File | Base | Tip | Change |
|:---|---:|---:|:---|
| `tests/test_paths.py` | 49 | 54 | +5 (WP2 D3/D4/D8) |
| `tests/deploy/test_cli.py` | 7 | 8 | +1, parametrized to 2 cases (D5) |
| `tests/test_current_migration.py` | 2 | 1 | **−1, deleted** |
| `tests/test_marine_feature_obs.py` | 3 | — | **−3, file deleted (a117db3)** |
| `tests/test_obs_cfg_surface.py` | — | 2 | +2, replaces the above |
| `tests/test_eval_segmented_lin_vel_gate.py` | — | 2 | +2 |
| `tests/test_student_gru_episode_boundary.py` | — | 4 | +4 |
| `tests/test_student_log_root.py` | — | 2 | +2 |
| `.hq/config/experiments/profile/test_*.py` | — | 48 | newly tracked, 9 files |

**Removed or weakened, with justification status:**

- `test_ou_update_shapes_on_shared_buffer` (ff47492). Removal justified and the message is
  accurate: I read the deleted body and it does reimplement the OU update inline and assert
  on its own three results, with no call into production. WP3 removed
  `_step_ocean_current_ou` and the `ou_*` knobs, so there is nothing left to gate. The
  module docstring was corrected in the same edit, which is the right discipline.
- `tests/test_marine_feature_obs.py`, 3 tests (a117db3, outside my commit list but inside
  my scope). Justified: WP1 deleted the Koopman marine-feature observation those tests
  covered. The replacement `test_obs_cfg_surface.py` is stronger than a deletion — it
  freezes the whole observation-toggle surface by AST and asserts the removed keys cannot
  return. Net −1 test for a removed feature.
- `test_cli_emits_json` weakened to a conditional skip. See F4.

No tolerance was widened and no assertion was silently dropped anywhere else in the diff.

**Did the 510-pass run test the worktree?** Yes for `constrained_albc`, and I verified the
import mechanism rather than assuming. `__editable___constrained_albc_0_1_0_finder.install()`
does `sys.meta_path.append(_EditableFinder)`, which places it after the stock `PathFinder`;
`python -m pytest` puts the invocation directory at `sys.path[0]`; the worktree root holds
`constrained_albc/__init__.py`. So the worktree package resolves first and
`/workspace/constrained-albc` is never reached. The green run is meaningful. The exception
is `marinelab`, covered in F3.

Two structural notes. There is no `pytest.ini` and no `[tool.pytest]` section, so the
48 newly tracked tests under `.hq/config/experiments/profile/` are not collected by
`pytest tests` and did not contribute to the 510. And `tests/deploy/conftest.py` stubs the
`constrained_albc` package with an explicit `__path__` computed from `__file__`, which is a
second, independent reason the deploy suite reads the worktree.

### 6. WP10a — is it mechanical?

Yes. I filtered all 28 changed files for added or removed lines beginning with a control
keyword (`if`, `for`, `while`, `return`, `break`, `continue`, `else`, `elif`, `try`,
`except`, `raise`, `assert`, `with`). Exactly one hunk matched:

```
-    assert eval_plots._RAD2DEG == 180.0 / np.pi
+    assert 180.0 / np.pi == eval_plots._RAD2DEG
```

That is ruff's Yoda-condition rule on a test assertion, semantically identical. Everything
else is imports, docstrings, whitespace, and Markdown under `docs/`. The commit also drops
tracked `__pycache__/*.pyc` files, which is a deletion of build artifacts and carries no
behaviour. No control flow changes.

### 7. Ledger completeness for this scope

Accurate: WP11, the `_REPO_ROOT` escape, the segmented refusal, and the deleted OU test each
have a CHANGELOG entry whose technical content matches what the diff does. The WP11 entry's
"bit-for-bit unchanged" needs the qualifier in F5. The five-tests-measured-the-wrong-tree
entry needs the qualifier in F3.

Gaps:

- **D3 and D7 appear in no CHANGELOG entry.** The "Six eval/deploy defects" bullet
  enumerates D2, D4, D5, D6, D8.
- **D8 appears in no commit message.** `3ebe129`'s subject and body list D2 through D7 and
  defer D9; the raise-on-corrupt-manifest change is implemented and tested but never
  declared there.
- Both documents say "six" while the union of what the diff implements is seven.
- The WP0 skip added to `test_cli_emits_json` is not recorded anywhere.

## (D) What I did not read

- `0004` WP1, `0005` WP3, `0006` WP5, `0007` WP4, `0008` WP6a, `0010` WP8, `0013` docs —
  read only where they touch `tests/` or explain a fix in my scope. The other reviewer owns
  the env/shim/Koopman semantics.
- `albc_cleanup_full.diff` in full (696 KB); I worked from the per-commit patches and
  targeted `git show` against the container.
- `marinelab_cleanup.diff` and `marinelab_CHANGELOG_head.md` — out of scope.
- The bodies of the 48 profile tests under `.hq/config/experiments/profile/`.
- **I did not search `scripts/`, `tools/` or the exam configs for callers of
  `eval.py segmented`.** My claim in C4 that the refusal breaks no working caller rests on
  `_vel_cmd_lin` being absent from every environment, which I did verify by enumerating
  every tracked `.py` at both `98dd2f2` and `ff47492`. A caller could still exist and would
  now fail loudly rather than silently — that is the intended behaviour, but it should be
  confirmed before merge.
- I did not run the test suite. All pass/skip counts quoted are the author's.
