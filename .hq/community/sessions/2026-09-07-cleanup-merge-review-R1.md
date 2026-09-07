# R1 — env / plant semantics + cross-repo coupling

Reviewer scope: WP0 (a5d6b41, db1bcc6), WP1 (a117db3), WP3 (04ef330), WP5 (3e35e9b),
WP4 (dcb658b), WP6a (fe5dfa2), WP8 (3c76df3) + marinelab (bcfb01a, 19016a5).
Read-only throughout. Live tree `/workspace/constrained-albc` confirmed still at
`d1fb67d`; nothing was written anywhere.

---

## (A) Verdict per commit

| Commit | Verdict | One-line reason |
|:---|:---|:---|
| a5d6b41 WP0 (omx profile in-repo, unpin adapter tests) | UNVERIFIED | 4,851-line patch; I read the file list and test hunks only, not the 2,079-line `analyze_training.py` or the 1,095-line `tslib.py` it adds. No env/plant code in it. |
| db1bcc6 WP0 (obs-oracle `_common` from `__file__`) | MERGE-SAFE | 9 lines in `tools/obs_oracle/dump_obs_oracle.py`; path resolution only, no plant surface. |
| a117db3 WP1 (koopman removal) | MERGE-SAFE | Both toggles defaulted off, appear in dumped configs only, never as an override. Obs width stays 72. |
| 04ef330 WP3 (dead knobs) | **NEEDS-FIX** | The `@property` decorator on `ConstraintEncoderRunner._should_log` was deleted along with the value-normalization block. Unlisted semantic change. Plus two stale-text leftovers. |
| 3e35e9b WP5 (delete `full_dof` + `tdc`, move controllers) | MERGE-SAFE | No live task id, script, or import reaches either package; the TDC controllers move with relative imports. |
| dcb658b WP4 (promote `envs/_core` to `constrained_albc/algorithms`) | MERGE-SAFE | Zero remaining importers of the old paths anywhere in code in the cleanup tree. |
| fe5dfa2 WP6a (delete `_pathsetup.py`) | MERGE-SAFE | Single consumer, and that consumer already required the path to be set before the re-insert ran. |
| 3c76df3 WP8 (albc side of `log_probs` drop) | MERGE-SAFE ONLY IF ATOMIC | Correct against new marinelab; both mixed states are hard errors. See finding 3. |
| bcfb01a + 19016a5 (marinelab side) | MERGE-SAFE ONLY IF ATOMIC | Same coupling, opposite direction. Old checkpoints still load; new ones do not load on old code. |

---

## (B) Findings, ranked

### F1 (HIGH, but currently masked) — WP3 deleted a `@property` decorator it did not mean to touch

Evidence, `commits/0005-WP3-...patch`, the tail of the
`constraint_encoder_runner.py` hunk:

```
-    # ------------------------------------------------------------------
-    # Properties
-    # ------------------------------------------------------------------
-
-    @property
     def _should_log(self) -> bool:
```

The section banner and the value-normalization helpers above it were the target;
the `@property` line belonged to `_should_log`, which survives. Confirmed on disk,
not only in the patch:

- base `98dd2f2:constrained_albc/envs/_core/runners/constraint_encoder_runner.py`
  has `@property` immediately above `def _should_log`.
- cleanup `HEAD:constrained_albc/algorithms/runners/constraint_encoder_runner.py:125`
  has `def _should_log` with no decorator.

Consequence: `self._should_log` is now a bound method, which is always truthy. The
three call sites (`:165`, `:176`, `:183`) all read it as a boolean, so each of them
is now a tautology instead of a guard.

Why it is masked rather than live: the only caller of `log()` is rsl_rl's
`OnPolicyRunner.learn`, which is itself guarded at
`/isaac-sim/kit/python/lib/python3.11/site-packages/rsl_rl/runners/on_policy_runner.py:154`
by `if self.log_dir is not None and not self.disable_logs:` — exactly the predicate
`_should_log` computed. So on the p5 training path the wrong answer and the right
answer coincide and nothing changes. The defect is that the class no longer enforces
its own contract, and any future call to `log()` from outside `learn()` (or any use
of `_should_log` in a new code path) silently gets `True`, including under
`disable_logs` on non-zero distributed ranks.

Failure scenario: a multi-GPU run where `disable_logs` is True on rank 1. Today
rank 1 never enters `log()`. If a later change calls `_log_constraint_metrics` or the
DORAEMON flush from anywhere else, rank 1 writes to `self.writer`, which is `None`
on that rank (`on_policy_runner.py:56`, only assigned at `:438` under the same
predicate), and the run dies with `AttributeError: 'NoneType' object has no attribute
'add_scalar'` on a rank whose stderr is usually not the one being watched.

Fix: restore the `@property` line. One line, no behavior question.

### F2 (MEDIUM) — three semantic changes are not in the CHANGELOG ledger

See section (C) answer 2. F1 is the one that matters; the other two are stale text
left pointing at deleted code.

### F3 (HIGH, process not code) — merging while the p5 chain runs kills the chain

`/workspace/g0c_runner/p5_common.sh` defines `EXPECT_HEAD=d1fb67d` and
`require_clean()`, which exits 2 unless `git -C /workspace/constrained-albc rev-parse
--short HEAD` equals that value AND `git status --short -- constrained_albc` is empty.
`grep -l require_clean` over `/workspace/g0c_runner/*.sh` returns `p5_common.sh`,
`p5_pack.sh`, `p5_smoke.sh`, `p5_teacher.sh`, `student_arm_p5.sh`.

Marker state on disk right now: `P5_SMOKE_DONE` and `P5_SMOKE_PASS` exist, `P5_DONE`
does not — the teacher stage is still running, and `p5stud` (which sources
`student_arm_p5.sh`) and `p5pack` are queued behind it in the `p5_chain.sh` tmux DAG.

Failure scenario: merge lands, HEAD moves off `d1fb67d`, teacher finishes and touches
`P5_DONE`, then `p5pack` and the student arm both exit 2 at their gate. The chain
stops silently at whatever stage was next, with a single FATAL line in
`/workspace/g0c_runner/status.log` and no other signal. This is the gate working as
designed; it is a reason to sequence the merge after the chain, not a code defect.

### F4 (MEDIUM) — the merge changes the dumped `env.yaml` key set, and `plantdiff.py`
compares key by key

`scripts/plantdiff.py` flattens both `env.yaml` files and compares
key-for-key, skipping only `('log_dir', 'run_name', 'seed', 'kl_ub',
'max_iterations', 'num_envs')` and any value longer than 120 chars. After the merge a
newly dumped `env.yaml` loses `ou_theta`, `ou_sigma`, `ou_enable`, `terrain`,
`use_marine_feature_obs`, `koopman_module_path`, and `agent.yaml` loses
`normalize_value`. All seven are present in the p5 smoke dump I read
(`/workspace/g0c_runner/experiments/rsl_rl/albc_trpo_teacher/p5_smoke/trpo_p5_smoke_s30_260907_130630/config/env.yaml:622-623`
for the koopman pair; `terrain: None` and `ou_enable: False` in the same dump).

Failure scenario: a post-merge arm is plant-diffed against a pre-merge incumbent to
prove "same plant"; seven spurious key differences appear and either mask a real one
or get waved away wholesale. Not a chain-breaker; worth a one-line note in whatever
does that comparison next.

### F5 (LOW) — WP3 left two pieces of text pointing at code it deleted

`constrained_albc/envs/main/albc_env.py` in the cleanup tree, `_init_tracking_buffers`:

- the docstring still reads `"""Manipulability, cumulative yaw, mid-episode dynamics,
  and OU process buffers."""`
- the method now ends on a dangling comment,
  `# OU process base current (mean-reversion target, set at reset)`, with nothing
  under it.

Cosmetic, but this branch's own stated rule (commit ff47492) is that a comment must
not outlive its body.

---

## (C) Answers

### 1. Behavior preservation on `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` with the p5 overrides

**Were the four removals really inert on that path — yes, all four, with evidence.**

- `ou_enable` / `ou_theta` / `ou_sigma`. Every code path that reads them is gated on
  `if self.cfg.ou_enable:` (five sites, `albc_env.py` :812, :1627, :1867, :1918,
  :2043 in the exp tree). The cfg default is `False`
  (`envs/main/config.py:624`), `config_simtoreal.py` does not mention `ou_` at all
  (grep returned nothing), and the p5 smoke dump records `'ou_enable': False`.
  No `.sh`, `.py`, or profile file in the launch surface sets it. So the OU branch
  never executed on this task, and deleting it is exact.
- `normalize_value`. Read once, `train_cfg.get("normalize_value", False)`, and the
  cfg value is `False` on `ALBCTRPORunnerCfg`. Every recorded `agent.yaml` I grepped
  under `experiments/legacy/` has `normalize_value: false`. Deleting the branch is
  exact.
- `_cmd_lin_scale` / `_cmd_att_scale` / `_cmd_yaw_scale`. Allocated as
  `torch.ones(...)` and never written anywhere after `f4583fd`; `lin` is written and
  never read, `att`/`yaw` multiply by exactly 1.0. Arithmetically identity. The
  branch's R7 fixed-action GPU replay is claimed byte-identical on all 10 arrays,
  which is the right check for this class; I did not re-run it.
- `terrain`. `grep -rn terrain --include='*.py' constrained_albc` in the cleanup tree
  returns nothing at all, and in the exp tree it appears only as the declaration. It
  is dumped (`'terrain': None` in the p5 smoke config) but never read.

**Does anything in the live launch surface still pass a removed Hydra key — no.**

I grepped `/workspace/g0c_runner` (all `*.sh` and `*.py`),
`/workspace/constrained-albc/scripts/*.py`, `.hq/config/experiments/profile/*`, and
the task registration in `constrained_albc/envs/main/__init__.py` for `ou_enable`,
`ou_theta`, `ou_sigma`, `normalize_value`, `_cmd_*_scale`, `terrain`,
`use_marine_feature_obs`, `koopman_module_path`. Every hit was in (a) package source
that the cleanup itself deletes, (b) a dumped `env.yaml` / `agent.yaml` / wandb log
from a past run, or (c) prose in `.hq/community/`. The p5 override set is exactly
three tokens plus the task id, all defined in
`/workspace/g0c_runner/p5_common.sh`:

```
'env.randomization.control_delay_steps=[0,13]'
'env.fault.thruster_always_dead=[0,3]'
'env.disturbance.enable=True'
```

None of the three is touched by this branch. **No Hydra-rejection defect found.**

Caveat worth stating: the seven §5 SimToReal overrides live inside
`envs/main/config_simtoreal.py` as a cfg subclass, not on the command line
(`envs/main/__init__.py:115-122`). That file is untouched by the cleanup and does not
reference any removed key, so it survives the merge intact.

### 2. Semantic changes in the diff that the CHANGELOG ledger does NOT list

Three, all from WP3, none of them large:

1. **The `@property` loss on `_should_log`** (finding F1). The ledger lists
   `normalize_value` and the HORA branch as the removal; it does not say that the
   surviving `_should_log` stopped being a property. This is the only one with a
   behavioral edge.
2. **The dangling `# OU process base current` comment and the stale
   `_init_tracking_buffers` docstring** (F5). The ledger claims the OU path was
   removed; two artifacts of it remain in the file.
3. **The blank line between `_init_command_buffers` and `_init_tracking_buffers`
   was consumed** by the `_cmd_*_scale` deletion hunk, leaving the two `def`s
   adjacent. Purely stylistic, and ruff evidently did not object, but it is a diff
   line that traces to nothing in the ledger.

I did not find any *removal* that the ledger omits. The ledger's coverage of what was
cut is accurate as far as my scope reaches.

### 3. Cross-repo coupling — `record_episodes` / `EpisodeBuffer.add`

**Every albc call site** (exp tree, `constrained_albc/envs/main/albc_env.py` unless
noted):

| Site | What it does |
|:---|:---|
| `:650` | allocates `self._episode_dr_log_probs` |
| `:1739-1743` | `self._doraemon.record_episodes(xi=..., returns=..., success=..., log_probs=...)` |
| `:1886-1889` | `xi_physical, log_probs = self._doraemon.sample(n)` then stashes `log_probs` |
| `envs/full_dof/albc_env.py:389, :1298-1302, :1378-1381` | the same four, in the package WP5 deletes |
| `tests/test_doraemon.py:179, :186, :194, :203, :212, :220` | `buf.add(..., log_probs=...)` and 4-tuple `get_all()` unpacking |

The cleanup branch updates all of the `envs/main` sites (WP8) and deletes the
`full_dof` ones (WP5). `sample()` is unchanged on both sides and still returns a
2-tuple; albc now discards the second element explicitly.

**Mixed state (a) — marinelab merged, albc not.** `DoraemonScheduler.record_episodes`
no longer accepts `log_probs`, so `albc_env.py:1739` raises
`TypeError: record_episodes() got an unexpected keyword argument 'log_probs'`.
`EpisodeBuffer.add` would fail the same way if reached. This fires on the first
`_reset_idx` that has finished episodes with DORAEMON active — i.e. after Isaac Sim
has booted and the first episodes have run out, a few minutes into a launch, not at
import. Loud, but expensive: a queued overnight stage dies after its GPU wait.

**Mixed state (b) — albc merged, marinelab not.** Old `record_episodes` still
declares `log_probs` as a required positional parameter, so the new 3-argument call
raises `TypeError: record_episodes() missing 1 required positional argument:
'log_probs'`, at the same point in the run. Also loud, also late.

Both directions fail hard and neither fails silently, which is the good news. The
requirement is that the two merges land together, before any launch — not that one
ordering is safer than the other.

**Does an old `doraemon_state.pt` still load — yes, verified.** In
`marinelab_cleanup.diff` the `load_state_dict` hunk removes exactly one line,
`self.buffer.log_probs[:n] = state["buffer_log_probs"].to(self.device)`, and reads
`buffer_xi`, `buffer_returns`, `buffer_success`, `buffer_write_idx` by key. An old
state dict simply carries one key nobody looks up, which Python ignores. The ledger's
claim holds.

**The reverse direction is a real hazard the ledger does not state.** `state_dict()`
no longer emits `buffer_log_probs`, so a checkpoint written by the NEW code and
resumed under the OLD code raises `KeyError: 'buffer_log_probs'`. This matters here
because the p5 family resumes DORAEMON from `doraemon_state.pt` beside the checkpoint
(`p3b_resume.sh` and `p3c_extend.sh` both hard-`exit 1` if that file is missing).
Once a post-merge run has checkpointed, rolling the repo back to pre-merge to resume
it will fail.

### 4. Conflict resolution, hunk by hunk

Nine hunks across three files. Naming below: "exp" = `origin/exp/koopman-marine-obs`
(the running p5 branch), "cleanup" = `cleanup/2026-09`.

**`CONFLICT_config.py`, one hunk (line 54).** exp keeps the name
`_FULL_DOF_CONSTRAINT_TERMS` and corrects the comment from `Probabilistic (5)` to
`(4)`; cleanup renames to `_MAIN_CONSTRAINT_TERMS` and keeps the stale `(5)`. Base
`98dd2f2:config.py:56-57` has the old name AND `(5)`, so each side fixed a different
half. **Both needed.** Resolve to:

```python
_MAIN_CONSTRAINT_TERMS: list[ConstraintTermCfg] = [
    # --- Probabilistic (4): binary indicator, budget = violation probability ---
```

**This hunk is a trap.** Cleanup's other two rename sites in the same file (the
`ALBCConstraintCfg(terms=...)` assignment and a comment) do not conflict and merge in
automatically as `_MAIN_CONSTRAINT_TERMS`. Taking the exp side here therefore produces
`NameError: name '_MAIN_CONSTRAINT_TERMS' is not defined` at import of
`envs/main/config.py`, which kills every task registration. `tests/test_constraints.py`
and `docs/reference/constraints.md` also carry the new name from cleanup.

**`CONFLICT_albc_env.py`, five hunks.** Four of them are the same shape: cleanup
deletes an `ou_*` block, exp added new p5 code immediately adjacent. Take exp's lines,
drop only the `ou_*` lines.

- Hunk 1 (:743, `_pre_physics_step`). Drop `if self.cfg.ou_enable:
  self._step_ocean_current_ou()`. **Keep** the `if self.cfg.disturbance.enable:
  self._step_fz_disturbance()` block.
- Hunk 3 (:979, method bodies). Drop `_step_ocean_current_ou`. **Keep all three of
  exp's new methods**: `_reset_fz_disturbance`, `_draw_fz_disturbance`,
  `_step_fz_disturbance`. This is the most dangerous hunk in the set — the cleanup
  side is empty, so a blanket "take cleanup" here deletes the entire PLAN item 11 Fz
  disturbance mechanism. Combined with hunks 1 and 5 (which remove its call sites in
  the same sweep) the result still imports and still trains; it just trains without
  the disturbance, and nothing says so. That is a silent plant change on the exact
  arm the p5 run exists to produce.
- Hunk 4 (:1520, `_log_midep_metrics`). Drop the two `Episode/current_*` lines.
  **Keep** `Dist/fz_abs_mean` and `Dist/strength_mean`.
- Hunk 5 (:1762, non-DR early-return path). Drop the `_ou_base_current` write.
  **Keep** `self._reset_control_delay(env_ids, None)` and
  `self._reset_fz_disturbance(env_ids, None)`.

- **Hunk 2 (:853, `_resample_commands`) is semantically incompatible and neither side
  can be taken.** exp changed the yaw command from a rate to a position: the merged
  context above the markers reads `yaw_lo, yaw_hi = self.cfg.yaw_cmd_range`, and
  `yaw_rate_cmd_range` no longer exists (the p5 smoke `env.yaml` dump has
  `yaw_cmd_range: [-pi, pi]` and no `yaw_rate_cmd_range`). Cleanup's side still says
  `* yaw_max`, a name that is not defined in the merged scope → `NameError` at first
  reset. exp's side still reads `self._cmd_att_scale` / `self._cmd_yaw_scale`, whose
  allocation cleanup deletes in a *non-conflicting* hunk → `AttributeError` at first
  reset. **Both naive resolutions crash.** The correct text is exp's semantics with
  the two identity factors dropped:

```python
        self._ang_cmd[env_ids, :2] = torch.empty(n, 2, device=self.device).uniform_(-1, 1) * att_max
        self._ang_cmd[env_ids, 2] = torch.empty(n, device=self.device).uniform_(yaw_lo, yaw_hi)
```

**`CONFLICT_eval.py`, three hunks.**

- Hunks 1 and 2 (:1905, :1936, the hover/zero-command setup and the per-step
  re-assert). exp introduced a latched hold-yaw (`_hold_yaw`) because the yaw slot is
  now a heading target; cleanup replaced the unguarded `_vel_cmd_lin` write with a
  `hasattr` guard. Take exp's yaw handling verbatim and wrap only the `_vel_cmd_lin`
  line: `raw_env._ang_cmd[:, :2] = 0.0`, `raw_env._ang_cmd[:, 2] = _hold_yaw`, then
  `if hasattr(raw_env, "_vel_cmd_lin"): raw_env._vel_cmd_lin[:] = 0.0`. Taking
  cleanup's `raw_env._ang_cmd[:] = 0.0` here would zero the heading target instead of
  latching it, which is the exact silent-void-the-hover-test failure exp's comment
  warns about.
- Hunk 3 (:2321, `run_segmented` cascade loop). exp writes
  `raw_env._ang_cmd[:, 2] = 0.0`; cleanup writes `= yaw_rate_cmd` plus the comment
  explaining why the `_vel_cmd_lin` writes below are deliberately unguarded. **This
  needs a human decision, not a mechanical merge.** Cleanup's commit e4ba44c makes
  `run_segmented` raise at setup on any env lacking `_vel_cmd_lin`, and on the merged
  tree no registered task has one, so this loop body is unreachable either way. The
  cheap resolution is to take cleanup's comment (it documents the refusal) with exp's
  `0.0` (consistent with exp's heading-target semantics), since the code cannot run.
  Flag it to whoever owns eval rather than deciding it in a merge commit.

### 5. WP4 move — anything outside `constrained_albc/` still importing the old paths?

**In code, no.** In the cleanup tree
(`/root/orca/workspaces/workspace/ponytail/constrained-albc`) I grepped `*.py`,
`*.sh`, `*.yaml`, `*.json` for `envs._core`, `envs/_core`, `envs.main.algorithms`,
`envs.main.encoder`, `envs.main.runners`, `envs.main.student`,
`envs.main.utils.logging`, `envs.main.utils.run_links`, `_pathsetup`,
`envs.full_dof`, `envs.tdc`. The only hits are inside `.graphify/.graphify_ast.json`,
a stale build index, not source. `envs/main/utils/__init__.py` survives as a genuine
module exporting only `derive_priv_obs_bounds_from_dr`, with a docstring pointing at
`constrained_albc.algorithms.utils` for the moved helpers.

**In docs, yes — about 20 sites**, and the branch knowingly rewrote some but not all.
Remaining stale references live in `docs/how-to/domain-randomization.md:91,213`,
`docs/how-to/sim-to-real.md:158`, `docs/explanation/system-overview.md:121-124`,
`docs/explanation/constraint-theory.md:6`, `docs/explanation/run-id-tree-design.md:100`,
`docs/architecture.md:41-45`, `docs/reference/reward.md:68,273,523,532`,
`docs/reference/domain-randomization-and-doraemon.md:67,462,463,623`,
`docs/reference/main-network-architecture.md:142,163,230,244,251,337,357-359`. Those
line numbers are from the **exp** tree (`d1fb67d`), which has not had the docs pass;
the cleanup branch's stat shows it edited most of these files, so a good fraction is
already handled on its side. I did not diff the docs file by file — the check I can
stand behind is the code one above.

`/workspace/g0c_runner` contains no reference to any old path (`grep` over its `*.py`
and `*.sh` returned nothing), so the launcher tree needs no change.

**`scripts/` is the one place the merge must not lose cleanup's side.** The exp tree's
`scripts/train.py:142,248`, `scripts/train_student.py:112-113` and
`scripts/play.py:93` still import through the shims (`constrained_albc.envs.main.runners`,
`.student.config`, `.student.runner`, `.utils`). Those shims are deleted by WP4, and
the cleanup branch updates all four call sites. None of these files is in the conflict
set, so the merge takes cleanup's version automatically — but if anyone hand-resolves
`scripts/` toward exp, training dies at import with `ModuleNotFoundError`.

---

## (D) What I did not read

Stated plainly so the lead can decide whether to cover it elsewhere.

- **`0001-WP0-...patch` (4,851 lines)** — I read the file list and the test-unpinning
  hunks. I did not read `analyze_training.py` (2,079 new lines), `tslib.py` (1,095),
  `metrics.yaml`, or the nine new `test_*.py` files it adds under
  `.hq/config/experiments/profile/`. That is the single largest unreviewed block in
  my scope. It adds files rather than changing plant code, which is why I ranked it
  last, but "UNVERIFIED" is the honest verdict.
- **`0006-WP5-...patch` (5,940 lines)** — I read the commit message, the full file
  list, and the `tdc_main/config.py` + `tdc_main/tdc_env.py` hunks. The other ~5,600
  lines are deletions of `envs/full_dof/**` and `envs/tdc/**`, which I verified by
  absence-of-references rather than by reading each deleted file.
- **`0007-WP4-...patch` (2,085 lines)** — I read the file list, the
  `student/config.py` and `runners/` deltas via the stat, and verified the outcome by
  grepping the resulting tree. I did not read the pure-rename hunks.
- **I did not re-run the R7 fixed-action GPU replay**, the pytest suites, or `ruff`.
  Every "byte-identical" and "503 passed" claim in this report is quoted from the
  commit messages, not independently reproduced. Doing so would require running in
  the cleanup clone, which the read-only constraint and the running chain both
  discourage.
- **I did not read the docs diffs line by line** (see answer 5), nor
  `0003-WP2`, `0011-WP10a`, `0012-WP11`, `0013`, `0014`, `0015` — those are outside
  my scope and belong to the other reviewer.
- **I did not verify the `.hq/config/experiments/profile/` directory for collisions**
  with anything the exp branch may have added under the same path. `git merge-tree`
  reported only three conflicting files, which is indirect evidence there is none.
