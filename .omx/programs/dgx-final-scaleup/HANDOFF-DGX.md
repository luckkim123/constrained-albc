# DGX handoff — ALBC final-teacher scale run (paste as-is into the DGX-side session)

You are the DGX-side session for the `dgx-final-scaleup` program of the constrained-albc project.
This document is self-contained: everything you need is here or produced by the commands below.
It carries the defaults `num_envs 16384, obs72 plant, current plant, purpose teacher_envscale_dgx,
seed 30`; **the act of sending you this document IS the workstation-side human approval of exactly
those defaults** (the workstation user answers PLAN §8 Q1/Q2/Q6 by choosing to send it — if you
received this some other way, STOP and ask). If any step below fails its check, STOP and report —
do not improvise a different run.

Evidence status as of 2026-08-04: all four pre-launch gates are closed, and the obs72 default is
settled on paired metrics (the obs76 teacher is genuinely better in isolation, but none of that
advantage survives distillation to a student — PLAN §1). Nothing in this document is awaiting a
further experiment.

## Hard rules

1. Launch EXACTLY ONE training run, the one specified in Step 3. Three things are pre-approved and
   are NOT exceptions you have to ask about: the optional Step 2 smoke, the Step 4b eval schedule,
   and a Step 5 crash relaunch. Anything beyond those three — a second training run, an
   off-schedule eval, a re-run at different settings — needs a new human approval.
2. Change NOTHING except the two knobs already decided and already written into the Step 3 command:
   `num_envs 16384` and `max_iterations 20000` (see 2b: the reservation is 10000). Every other "scale-up companion" change was tested
   and rejected on record: kl_ub-up is known-bad (E1), performance_lb re-derivation belongs to the
   next purpose, DR-box widening is blocked pending measured hardware bounds, entropy/min_std
   changes were a 5/5 zero-adoption sweep, num_mini_batches stays 4, step_interval stays 250. If you
   think a knob needs to differ, that is a STOP-and-report, not a judgment call.
   Do not "correct" `max_iterations` back to 5000. That rule of thumb is not merely withdrawn on
   paper — it is now **measured false on this plant**. `trpo_iterbudget_s30_260805_012813`
   (2026-08-05) resumed the reference teacher 4999 -> 9998 with nothing changed but the budget, and
   the anchored paired eval returned **six REAL flags, all better, all at hard DR**, with hard
   `att_norm` dispersion falling 2.3782 -> 0.6524 (a **73 % cut**) and nothing REAL at
   none/soft/medium. Extending is the strongest measured lever this project has. The old rule of thumb
   that iteration-extension is net-negative (extend8k, moreiters) is WITHDRAWN — PLAN §3 retracted it because `moreiters` was
   cited backwards (it IMPROVED at the fair `none` level), the effect's sign is
   `performance_lb`-dependent, and both datapoints sit on the retired posttam plant. 20000 is a
   recorded user decision (2026-08-04) whose risk is carried by Step 4b's gates, not an unreviewed
   extension.
2b. **DECISION GATE AT ITERATION 10000 — do not skip it, and do not treat 20000 as a commitment.**
   `max_iterations` is a pure loop bound (verified: `constraint_trpo.py:636-642` is a lone
   `logger.info`; DORAEMON never reads it), so the first 10000 iterations of this run are identical
   to a 10000-iteration run. Two things follow. First, **10000 is where this run becomes readable**:
   the workstation reference `trpo_iterbudget_s30_260805_012813` is 4096 envs x 10000 iterations on
   this exact plant, so the 10000 checkpoint differs from it in `num_envs` ALONE and is the
   comparison the run exists to make. Second, everything past 10000 is an unmeasured regime — the
   curriculum saturates at ~7748 and the mechanism behind the measured gain is exhausted there.
   So: at iteration 10000 (~48 h, 2.0 days at 16384 — see the wall-clock note below), STOP AND
   REPORT with the checkpoint and the eval. Continuing to 20000 costs a second ~2 days and is a
   separate human decision, not the default. **The machine is reserved for 10000, not 20000**
   (user decision 2026-08-05).
   The larger number is written into the command only so that a still-climbing curve does not
   require a resume.

3. `isaaclab/` is a pristine fork — never commit or write project files into it.
4. All numbers you report are single-seed screening on a non-reference machine (a +109%
   cross-machine isolation term is on record). Report measurements, never adoption conclusions.

## Machine specifics (GB10, verified on record)

- No Docker; Isaac Sim is a source build. Launcher: `TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p`
  (raw python lacks numpy; missing TERM kills the launcher over SSH with "unknown terminal type").
- Single GPU — do NOT set `CUDA_VISIBLE_DEVICES`.
- Unified 124,610 MiB memory: `nvidia-smi` reports Memory-Usage "Not Supported". Monitor with
  `free -m` and `nvidia-smi --query-compute-apps=pid,used_memory`. The only MEASURED training peak is at 32768
  envs: 83,170 MiB, leaving ~41,400 MiB spare (the source figure carries a 1,000 MiB internal
  inconsistency). **This run is 16384**, so env-side memory should land near 42,000-45,000 MiB with
  large headroom — but that is an interpolation: read it off the first `free -m` and report the real
  number instead of assuming it. Abort signal: `free -m` "used" above **102,400 MiB**. Every memory number here is
  in MiB because that is the unit `free -m` prints — do not convert to GB by eye, the headroom is
  only ~41 GB and a GB-vs-GiB slip is ~7% of it. A Step 4b eval starts a SECOND Isaac Sim process on
  this same pool; see the eval-contention exemption in Step 4b before reading a spike as an abort.
- Expected steady-state: **~17.3 s/iter at 16384 — an INTERPOLATION, not a measurement.** The only
  measured DGX point is 34.73 s/iter at 32768; 16384 is assumed to be half. Replace it with the real
  number inside the first 100 iterations. At ~17.3 s/iter, **10000 iters ≈ 48 h ≈ 2.0 days** and the
  20000 cap would be ≈ 96.5 h ≈ 4.0 days. **If sustained s/iter exceeds ~22, the interpolation is
  wrong — report before continuing rather than silently running long.** That figure is a CAP,
  not a fixed commitment: Step 4b's periodic eval + stop rule can end the run earlier
  (at ~17.3 s/iter: 24 h at 5000, 48 h at 10000, 72 h at 15000) with no loss, because every earlier
  checkpoint is on disk. Note 5000 is BELOW curriculum saturation (~7748) and is not a useful
  stopping point on merit — it is listed only for costing.
  Plan for exclusive occupancy of about a week and make sure nothing else needs the GPU.
- cuDNN: the container-side cu13-vs-cu128 conv1d bug does NOT exist on DGX, but verify once before
  trusting any conv path: `python -c "import torch; print(torch.backends.cudnn.version())"` via the
  isaaclab launcher and record the value.

## Step 0 — sync and provenance (blocking)

```bash
git -C ~/workspace/constrained-albc pull --ff-only     # workstation has pushed main first
git -C ~/workspace/marinelab pull --ff-only
git -C ~/workspace/constrained-albc status --short --branch   # MUST be clean, on main
git -C ~/workspace/constrained-albc rev-parse --short HEAD    # record this sha in your report
```
If the tree is dirty or a pull fails, STOP and report. A dirty launch already voided one 4.9 h
run in this project.

## Step 1 — expected plant (verify BEFORE burning GPU time)

The run must train the gen-1 final-teacher recipe (E-int lineage, obs72, current plant). After
Hydra dumps the run's `env.yaml`/`agent.yaml` (they appear in the run's log dir at startup),
verify EVERY row of this table against the dumped values. One mismatched row = kill the run,
report the diff. Do not trust branch topology — experiment branches have deliberately reverted
adopted values before; only the dumped config counts.

| Key | Expected |
|:--|:--|
| observation width (env.yaml observation_space) | 72 (NOT 76; `use_extra_policy_obs` false/absent) |
| fault.enable | true |
| fault.thruster_fail_prob / thruster_health_range | 0.1 / (0.0, 0.5) |
| use_privileged_fault_obs (env-cfg ROOT key, NOT under `fault.`) | false |
| max_thrust_scale DR band | (0.85, 1.15) |
| doraemon: enable / kl_ub / performance_lb / step_interval | true / 0.12 / 250.0 / 250 |
| doraemon alpha / buffer_size / min_episodes | 0.5 / 2000 / 200 |
| DR box (spot-check) | added_mass_scale (0.5,1.5), damping (0.4,1.7), inertia (0.4,2.0), volume/body_mass/buoy (0.75,1.25), water_density (995,1025), payload_mass (0,3), thrust_coefficient_scale (0.7,1.3) |
| agent: num_steps_per_env / max_kl / cg_iters / num_mini_batches / num_learning_epochs | 64 / 0.005 / 10 / 4 / 5 |
| agent: value_lr / max_grad_norm / init_noise_std | 1e-3 / 1.0 / 0.7 |
| agent: min_std_per_dim / entropy_coef_per_dim | (0.10, 0.10, 0.05 x6) / (0.01, 0.01, 0.001 x6) |
| encoder | hidden [256,128,64], latent 9, elu, output_norm true, privileged_dim 28 |
| seed | 30 |
| save_interval | 50 |
| num_envs | **16384** (user decision 2026-08-05; the earlier 32768 is superseded) |
| max_iterations | 20000 in the command, **10000 reserved** — these are not in conflict: the flag is a pure loop bound, so the run is stopped at the 10000 gate (2b) unless a human decides otherwise. Do not lower the FLAG below 20000; do not run past 10000 without that decision |
| resume | false |

Note: `policy_obs_dim=69` in agent.yaml is a stale static default — the runtime truth is
env.yaml's observation_space. Do not flag 69-vs-72 as a mismatch.

## Step 2 — memory/throughput sanity (optional but cheap)

If you want a pre-flight, a 50-iter smoke at 16384 envs with `--logger` disabled is acceptable
(record s/iter and `free -m` peak, then kill). Do NOT reuse its run dir for the flagship.

## Step 3 — launch

```bash
cd ~/workspace/constrained-albc
TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 \
  --num_envs 16384 --max_iterations 20000 --headless \
  --run_group teacher_envscale_dgx \
  --logger wandb --log_project_name teacher_envscale_dgx \
  env.fault.enable=True \
  agent.run_name=dgx16k_s30
```

- **`env.fault.enable=True` is REQUIRED and is not optional polish.** `FaultInjectionCfg.enable`
  defaults to `False` in code (`envs/main/config.py`, `ALBCEnvCfg.fault = FaultInjectionCfg()`), so
  without it the env comes up fault-DISABLED and fails the `fault.enable | true` row of the Step 1
  table. (`train.py` also has a `--fault` store_true flag that sets the same field; either works.
  Use the Hydra override above — it is the string on record for the runs this one must match.)
  The E-int final teacher and the
  Phase D obs76 teacher were both launched with exactly this override; omitting it is the same diff
  that voided a 4.9 h run and made `trpo_obs76_s30_260803_233239` VOID. Step 1 will catch it, but
  only after the env has been built — verify the dumped `env.yaml` rather than assuming.
- run_id is minted at train time by make_run_id (`trpo_dgx16k_s30_<ts>`); record the actual id
  from the created log dir immediately — every watcher/report keys on it.
- `--run_group` and `--log_project_name` carry the SAME string (group = wandb project = purpose).
- Run it inside tmux/nohup so SSH drops don't kill it; capture stdout to the run's `launch.log`.
- Watcher discipline: poll the training PID (a pgrep pattern can self-match), and scope any NaN
  grep to metric lines only.

## Step 4 — iteration-500 abort gate (~4.8 h in)

By iteration 500 two DORAEMON updates have occurred. Read these TB tags (names verified against a
real event file): `DORAEMON/kl_step`, `DORAEMON/success_rate`, `DORAEMON/mode`,
`DORAEMON/ess_ratio`, `Policy/entropy`, `Policy/mean_noise_std`, `Loss/kl`,
`Policy/line_search_success`, `Loss/value_function`, `Loss/cost_value`,
`Constraint/barrier_penalty`.

KILL the run and report if ANY of:
- `DORAEMON/kl_step` shows no accepted widening move (≈0 on both updates) AND `DORAEMON/mode` <= -2;
- `DORAEMON/success_rate` pinned > 0.95 (inert gate) or < 0.5 (infeasible) sustained;
- any DR dim already at Beta(1,1) (premature saturation);
- s/iter > 40, or `free -m` used > 102,400 MiB — in either case sustained for 15+ min and measured
  OUTSIDE an eval window (Step 4b's exemption; a 9-min eval legitimately moves both numbers);
- NaN in metric lines.
Healthy expectations: success_rate ≈ 0.75–0.90 (anchor measured 0.815 at lb=250),
kl_step at the 0.12 cap on accepted updates, `DORAEMON/ess_ratio` HIGHER than workstation runs
(buffer window narrows ~11 -> ~2.9 iters at 16384 envs, ~1.4 at 32768 - expected, not an anomaly).

Repeat a lighter look at ~iter 1000 and ~2500 (checkpoints land every 50 iters ≈ 29 min).

### Step 4b — the three gates that matter for a 20000-iteration run

This run is reserved for 10000 iterations (~48 h ≈ 2.0 days at 16384; the 20000 cap would be ~4.0 days). The curriculum is expected to finish expanding
around iteration 7750, so roughly two thirds of the run trains on a frozen, fully-expanded DR box.
That regime has never been run at this length, and 17,500 of the 20,000 iterations happen after the
last Step 4 look at iteration 2500 — these three gates are what make that stretch safe.

**Gate A — saturation checkpoint (~iter 7750–8000). This is the gate that decides what kind of run
this is.** `max_iterations` is DORAEMON's expansion clock, so until the box saturates, raising it is
a DR-WIDTH treatment, not extra training. Once the box hits its Beta(1,1) ceiling the treatment
stops and everything after is purely more optimization on a STATIONARY target — which is the regime
this run is meant to be in for its last two thirds.

Confirm `DORAEMON/kl_step` has gone to 0 and `doraemon_state.pt` reads Beta(1,1) on every dim
(`torch.load`, keys `dist_a`/`dist_b`).

**Primary reference — measured on THIS plant** (`trpo_iterbudget_s30_260805_012813`, 2026-08-05,
4096 envs, E-int resumed 4999 -> 9998, fault DR on, 21 DORAEMON dims). The box saturated at
**iteration 7748**: 30 chain expansions (29 of them exactly at the `kl_ub` = 0.12 cap, the 30th a
partial 0.0410 step onto the ceiling) for a total KL budget of **3.5209**, and `doraemon_state.pt`
reads Beta(1,1) on **21 of 21** dims. Over the following 2250 iterations `DORAEMON/entropy_before`
took exactly TWO distinct values (-18.23835 then -18.200739 constant) and nine further boundaries
fired with `mode` = 0 and `kl_step` = 0 — the scheduler kept deciding "expand" with nothing left to
expand into, which is how saturation is distinguished from a stall.

Two things this changes for the flagship. First, **the shipped teacher E-int never reached its own
ceiling**: at iteration 5000 it had 0 of 21 dims at Beta(1,1) and had spent 2.2800 of the 3.5209
budget (65 %), with the four nominal-0 dims still bunched near zero (`fault_severity` at
Beta(1, 10.099), mean 9 % of range). The 20000-iteration budget is therefore not merely "more of the
same" — it is the first run on this plant that trains against the fully-expanded box. Second, the
saturation point sits ~1000 iterations later than the older plant below, because this plant carries
one extra DR dim.

The measurement is at 4096 envs on a resumed chain; the boundary schedule is iteration-based and
`kl_ub`-capped so it should carry to 16384 envs from scratch, but the feasibility gate that decides
whether a boundary expands or contracts is env-count sensitive. Treat 7748 as the expectation, not a
guarantee.

Corroborating case on the RETIRED posttam plant (`trpo_biasema_extend8k_260716_162849`,
from-scratch, 4096 envs, 20 dims): 26 boundaries
fired, the LAST at iter 6750, and the freeze was total — over the remaining 1250 iterations
`DORAEMON/entropy_before` took exactly TWO distinct values (-18.2939 then -18.2007 constant),
`success_rate` held 0.813 -> 0.789 (min 0.7595), `Train/mean_reward` held 258-268. A saturated box
really does stop moving; nothing degraded in that stretch.

**Read that `Train/mean_reward` band as p5-p95, not as limits** (re-measured 2026-08-05 over the same
1250 post-saturation iterations): p5 258.2, median 263.8, p95 268.8, but the FULL excursion is
**251.4 to 273.7**. A single point at 253 or 272 is inside what the healthy reference run itself did
and is not a Gate-A finding. What matters is a monotone trend, not an excursion — judge the slope
over a few hundred iterations, not one sample against the band edge.

On the current plant the same post-saturation stretch (2250 iterations) ran **236.4 to 265.0, ending
258.6** — a wider and lower band than extend8k's, for the same reason the success band moved: one
more DR dim makes the saturated exam harder. Judge this run against 236-265, and against the slope
rather than either edge.

- Saturated MUCH earlier than ~7000: the budget arithmetic is wrong — report, do not kill.
- NOT saturated by ~iter 10000: **this is the failure that matters**, not a scheduling curiosity.
  (Threshold moved from 9000 on 2026-08-05 to keep the same ~30 % margin over the measured 7748.)
  The recorded case is `trpo_e3_extend10k_260713_224822` (a converged teacher RESUMED for +10000):
  boundaries kept firing to iter 14749 and never stopped, because `success_rate` fell under alpha so
  the box was pulled back instead of reaching the ceiling — `entropy_before` -30.1 -> max -18.24 ->
  back to -24.4, success ending 0.37, reward 274 -> ~225. That run trained 10000 iterations against
  a NON-STATIONARY target. If this run is still firing boundaries past ~9000, it is in that regime,
  not in extend8k's — report immediately.

Note on reading `DORAEMON/kl_step`: `doraemon.py:416-419` writes `kl_step = 0.0` on every
NON-boundary iteration, so sampling the tag at a fixed stride can read 0 everywhere and look like
"no expansions". Scan for `kl_step > 0` over ALL steps instead. On a resumed run the boundaries are
phase-shifted (extend10k fires at iters ending 249/499/749/999, not 250-multiples).

**Gate B — inert-gate watch, at every eval point below.** `DORAEMON/success_rate` sustained > 0.95
is the recorded inert-gate failure class: `performance_lb=250` has stopped constraining anything
and the rest of the run is unguarded. The reference teacher already sits at 0.814 against
`alpha=0.5`, so there is not much slack. If it pins > 0.95: KILL the run, keep the best checkpoint,
and report — the same action as the Step 4 gate, because an inert gate means every remaining
iteration is unguarded and the checkpoints already on disk lose nothing.

**Watch the LOW side just as hard, and at every eval point — not only at iteration 500.**
`success_rate` sustained BELOW alpha 0.5 is the mechanism that prevents saturation: DORAEMON
contracts the box instead of reaching the ceiling, Gate A never closes, and the run spends its
remaining days chasing a moving target (extend10k: success decayed 0.91 -> 0.38 monotonically,
crossing alpha around iter 8250 and never recovering, with `Train/mean_reward` 274 -> ~225).
**Healthy reference at saturation on THIS plant is 0.62-0.70, NOT the 0.76-0.81 of the retired
posttam plant** (corrected 2026-08-05 from `trpo_iterbudget_s30_260805_012813`: 0.699 at the
saturation iteration, min 0.6215, 0.666 at the end). Judging this run against 0.76-0.81 would raise
a false alarm on a perfectly healthy run — the extra `fault_severity` dim makes the fully-expanded
exam harder, so the same policy settles lower.

Read the SHAPE, not the level. On the healthy reference `success_rate` falls monotonically
0.890 -> 0.699 **while the box is still expanding**, then goes flat once the box freezes. That
decline is the exam getting harder and is expected. The failure signature is a decline that
**continues after saturation**, or one that continues **while boundaries are still firing** past the
point they should have stopped — report either before it reaches alpha, not after.

**Gate C — policy-health watch, at every eval point. There is NO automatic early stop anywhere in
this codebase**, so a policy that quietly degenerates burns the remaining days at full cost. Nothing
in the algorithm halts training: a non-finite TRPO step logs a warning and SKIPS that update
(`constraint_trpo.py:560-565`), a failed line search reverts and continues, a DORAEMON ESS failure
reverts only the DR update. The run reaches `max_iterations` unless a human kills it. Also note
`Policy/entropy` and `Policy/mean_noise_std` are NOT scheduled — the action log_std is a LEARNED
TRPO parameter re-clamped every update to [min_std_per_dim, 2.0] (`:506-511`), so over 4x the usual
number of updates it can drift where a 5000-iteration run never had time to. Read all three at every
eval point:
Measured reference band (read these before judging anything). `mean_noise_std` starts at
`init_noise_std` 0.7 and decays FAST and then asymptotes; the decay rate is not a function of
`max_iterations`, so this shape is what to expect at any length:

| iteration | E-int, current plant, 4096 envs | extend8k, retired posttam plant, 4096 envs |
|--:|--:|--:|
| 1000 | — | 0.1244 |
| 2000 | — | 0.1010 |
| 3000 | 0.0945 | 0.0915 |
| 5000 | 0.0881 | 0.0860 |
| 8000 | — (run ended) | 0.0838 |

The hard floor is **0.0625** (`min_std_per_dim` = (0.10, 0.10, 0.05 x6) averaged over 8 dims). No
recorded run has ever approached it: extend8k's decay rate FALLS from about -1.3e-6/iter before
iteration 5000 to about -6e-7/iter at 7500-8000, and carrying that measured rate forward puts
iteration 20000 near **0.076**, still above the floor. (A naive linear extrapolation from the
pre-5000 slope would instead predict floor contact around iteration 18000 — the measured 5000-8000
segment contradicts it, which is exactly why this needs watching rather than predicting: the run
goes 12000 iterations past any measurement that exists.) Note the DGX run uses 16384 envs, so its
trajectory will NOT overlay E-int's — treat the band as indicative, not as a pairing.

**The aggregate tag alone is a weak instrument — use the per-dim read.** On recorded posttam runs
**5 of the 8 action dims already sit exactly ON their per-dim `min_std` floor**; only {arm1, thr0,
thr3} are free. So `Policy/mean_noise_std` is an average dominated by already-clamped dims and it
cannot move much by construction. At each eval point also read the checkpoint directly and report
HOW MANY of the 8 dims sit at their floor:

```python
import torch
sd = torch.load("model_<it>.pt", map_location="cpu", weights_only=False)["model_state_dict"]
std = sd["log_std"].exp()          # shape [8]; the key is log_std, not std
floors = torch.tensor([0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
print(std.tolist(), int((std <= floors * 1.01).sum()), "of 8 floored")
```

Verified reference — the E-int teacher this run must match, `model_4999.pt` on the current plant:
`[0.1003, 0.1470, 0.1316, 0.0500, 0.0500, 0.1257, 0.0500, 0.0500]` = **5 of 8 floored**, free set
{arm1, thr0, thr3} (dims 1, 2, 5). Their mean is 0.0881, which is exactly the `mean_noise_std` tag
at that iteration — so the aggregate and the per-dim read agree, and the aggregate is simply the
less sensitive of the two. Going from 5/8 to 7/8 or 8/8 floored is the real signal; the aggregate
would barely register it.

Also note this is a known-open phenomenon, not a new risk: sigma has tightened monotonically across
campaigns (0.22-0.34 in April, 0.175 in June, 0.109 on 2026-07-13, 0.084 by 2026-07-16) and the omx
wiki records it as never solved. It has nonetheless been benign for every converged teacher so far —
extend8k held reward 258-268 and success ~0.79 through its post-saturation stretch with sigma at
0.084, and the 2026-08-05 run on the current plant held reward 236.4-265.0 (ending 258.6) and
success 0.62-0.70 through 2250 post-saturation iterations. Report movement; do not treat a floored
dim as an automatic fault.

What to report:
- `Policy/mean_noise_std` **below ~0.070**, or the per-dim floored count rising above 5/8 =
  exploration is being taken over by the clamp rather than learning.
- `Policy/entropy` falling with no deceleration across two eval points. The reference shape
  decelerates hard: extend8k drops 1.42 over iterations 2000-5000 and only 0.14 over 5000-8000.
- `Policy/line_search_success` sustained low = TRPO rejecting nearly every step, policy frozen while
  wall-clock burns. This one is PRECAUTIONARY: it reads exactly 1.000 at every recorded iteration of
  both reference runs, so any sustained departure is unprecedented and worth reporting early.

None of these is an automatic kill — they are the readings that tell a human whether the remaining
days are buying anything.

**Periodic eval + stop rule (this is what bounds the 8 days).** Evaluate at iterations
5000 / 7500 / 10000 / 12500 / 15000 / 17500 / 20000 (~9 min each at 64 envs) and track `none`-level
`att_norm ss_error` from each eval's `summary.json`. **Two consecutive eval points worse than the
running best by MORE THAN 0.10 deg each = stop the run and keep the best checkpoint.** The 0.10 deg
term is the project's registered `ss_error` decision floor (`_analyze/recompute_metrics.py`
`DECISION_FLOORS`); without it the rule fires on a 0.01 deg wobble and ends an 8-day run at 96 h.
A point that is worse by less than the floor is NOT worse — it counts as a tie, and the running best
is unchanged. Stopping early costs nothing: the better checkpoint is already on disk, and the run's
earlier iterations are bit-identical to a shorter run at the same seed and `num_envs` (verified: the
5000-iter and 8000-iter biasema pair agree to 0.000000 on `Policy/entropy`, `mean_noise_std`,
`line_search_success` and `DORAEMON/kl_step` at every sampled iteration up to 4999).

Do NOT read that as "20000 is just 5000 trained longer", though. Until the box saturates,
`max_iterations` is DORAEMON's expansion clock, so raising it administers a WIDER DR box — the
treatment, not the duration, is what changed in every recorded extension. The run becomes a pure
train-longer run only AFTER Gate A closes. Both statements are true and they matter at different
ends: the prefix is identical (so stopping early is free), the endpoint is a different DR exposure
(so the final policy is not "the 5000 policy, more converged").

**Eval contention — the Step 4 abort thresholds are SUSPENDED during an eval.** Each eval starts a
second Isaac Sim process on the same single GB10 and the same unified memory pool, so `free -m`
"used" rises and s/iter degrades for the ~9 min it runs. That is expected contention, not the
failure the abort gate is looking for. Record the start/stop wall-clock of every eval, exclude those
windows when judging the memory and s/iter thresholds, and only treat a reading as an abort signal
if it persists 15+ min after the eval process has exited. The NaN and DORAEMON conditions are NOT
suspended — they still apply during an eval.

**Fair-exam rule — do not skip this.** `eval.py static` defaults `--doraemon-dr` to True, which
grades each checkpoint on the DR box THAT checkpoint learned. Checkpoints from different iterations
therefore sit at different curriculum widths and their soft/medium/hard numbers are NOT comparable
to each other. Compare only on `none`, or re-evaluate every checkpoint under
`--doraemon-dr-from <one fixed run dir>` so they all take the identical exam.

Two mechanics make this sharper than it sounds, both worth knowing before you trust any DR-level
number from a mid-flight eval. (a) The auto-load reads the run's TensorBoard event file and takes
the FINAL `DORAEMON/mean/*` values in it (`analysis/dr_config.py:214-241`), so on a run that is
still training, even the SAME checkpoint evaluated at two different wall-clock times gets two
different exams. (b) `doraemon_state.pt` is written to the run dir and OVERWRITTEN at every save
(`constraint_encoder_runner.py:293`), so an early checkpoint's own box is not recoverable from it
afterwards — only `curriculum_trajectory.json` (written beside it) preserves the full trajectory.
`none` is unaffected by all of this, which is why it is the comparison axis.

## Step 5 — crash handling

A relaunch mints a NEW run id — never resume by editing Hydra `agent.resume` or a group-path
`load_run` (both fail silently). The working protocol:

```bash
cd ~/workspace/constrained-albc
# RESUME_SRC MUST sit at the EXPERIMENT ROOT, NOT inside the run_group dir:
ln -s <abs_path_to_crashed_run_dir> logs/rsl_rl/albc_trpo_teacher/RESUME_SRC
TERM=xterm ~/workspace/isaaclab/isaaclab.sh -p scripts/train.py \
  --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 16384 --headless \
  --resume --load_run RESUME_SRC --checkpoint model_<last>.pt \
  --max_iterations <20000 minus completed iters> \
  --run_group teacher_envscale_dgx --logger wandb --log_project_name teacher_envscale_dgx \
  env.fault.enable=True \
  agent.run_name=dgx16k_s30_resume
```

Three things about this command are load-bearing; getting any of them wrong is worse than the crash.

- **`env.fault.enable=True` is REQUIRED on the resume too.** `--resume` restores WEIGHTS ONLY:
  `train.py` builds the env from the Hydra config first (`train.py:264`) and only then calls
  `runner.load(resume_path)` (`train.py:305`) — nothing restores the crashed run's env config. Omit
  the override and you resume a fault-DISABLED plant, which is exactly the diff that voided a 4.9 h
  run and made `trpo_obs76_s30_260803_233239` VOID. After the relaunch, **re-run the Step 1 table
  against the RESUMED run's dumped `env.yaml`** — Step 1 is not a launch-only check.
- **The symlink goes at the experiment root**, `logs/rsl_rl/albc_trpo_teacher/RESUME_SRC`.
  `get_checkpoint_path` scans `log_root_path` directly with `os.scandir` + `re.match` on the entry
  name (`isaaclab_tasks/utils/parse_cfg.py:193-195`), and `log_root_path` does NOT include the
  `--run_group` layer (`train.py:216`). Putting it beside the run dirs inside
  `teacher_envscale_dgx/` is one level too deep and fails with
  `ValueError: No runs present in the directory`.
- **`--max_iterations` on a resume is the REMAINING count**, not the target: rsl_rl computes
  `tot_iter = start_iter + num_learning_iterations` from the checkpoint's stored `iter`.

Pick `model_<last>.pt` by NUMERIC sort (`ls model_*.pt | sort -t_ -k2 -n | tail -1`) — alphabetical
sort has destroyed final checkpoints before. Record both run ids and the stitch point in your report.

What survives a resume and what does not (`doraemon.py:773-811`): the Beta distribution, the
`step_count` phase, the episode buffer and `total_episodes` are all restored, so the curriculum
resumes at the right point and the boundary schedule is NOT re-phased. The plant config is NOT
restored (the bullet above). And `_trajectory` is NOT in `state_dict()` either — so the resumed
run's `curriculum_trajectory.json` contains ONLY post-resume boundaries. Keep the crashed run's
directory: after a resume, the full curriculum record is the crashed run's trajectory file plus the
new one, and neither is complete alone. Say so explicitly in your report.

## Step 6 — after the run

1. Verify the LAST checkpoint exists by NUMERIC sort (`model_19999.pt` for a full run, or whatever
   the stop rule left), plus `doraemon_state.pt`, `curriculum_trajectory.json`, and the wandb dir.
2. Do NOT delete or trim anything — all ~400 checkpoints (5.9 MB each, ~2.4 GB total) are the
   dose-response series and are the main deliverable alongside the final model.
   `curriculum_trajectory.json` matters as much as the checkpoints: `doraemon_state.pt` only ever
   holds the LATEST box (it is overwritten at every save), so the trajectory file is the sole
   record of which box each mid-run checkpoint learned under. If the run was resumed, that record
   is SPLIT — the trajectory is not carried across a resume (Step 5), so keep and sync BOTH run
   directories.
3. Sync back to the workstation (the workstation runs the paired eval under its shared-DR
   protocol): the full `logs/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/<run_id>/` dir and the
   `experiments/` mirror entry. If you eval locally, use exactly
   `eval.py static --seed 42 --num_envs 64 --headless` with the checkpoint path THROUGH the
   run's `train` symlink, and NEVER pass `--output_dir`.
   Note: the workstation's eval carries a cross-run pairing fix (per-level reseed) that landed
   after this repo state was branched; a local eval on an older `eval.py` will NOT be paired with
   the workstation's reference evals. Report your local numbers as indicative only.

## Step 7 — report back (measurements only)

- run_id, sha, exit code, wall-clock, s/iter curve summary, `free -m` peak;
- abort-gate readings at 500/1000/2500, then Gate A (saturation, ~7750), Gate B (inert-gate watch)
  and Gate C (`Policy/mean_noise_std`, `Policy/line_search_success`, `Policy/entropy`) at every
  eval point;
- **the dose-response table** — for each eval point (5000/7500/10000/12500/15000/17500/20000, or
  wherever the stop rule fired): iteration, `none`-level `att_norm ss_error`, `roll ss_error`,
  `roll os_env_mean`, `n_gt20`, `survival_pct`, and which checkpoint you judged best. This table is
  the run's primary scientific output — it is the first iteration-budget curve ever measured on
  this plant;
- final DORAEMON state: per-dim Beta a/b, the iteration at which the box saturated, achieved
  expansion count (nonzero `DORAEMON/kl_step` entries — NOT the number of scheduled boundaries),
  and final success_rate;
- checkpoint inventory (numeric sort) + doraemon_state.pt + wandb sync status;
- any deviation from this document, however small.

No adoption language: the standing rule says a DGX-trained teacher is not the shipped final model
(cross-machine +109% term); this run is scale exploration unless the workstation side says
otherwise.
