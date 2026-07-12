# Glossary

> Alphabetized term list for the `constrained-albc` codebase. Each entry is 1-2
> lines with a link to the owning reference page where one exists. Numbers
> (dims, ranges, task IDs) live in the linked reference page, not here — this
> page defines terms, it does not restate values.

---

**ALBC** — This project's arm-equipped underwater vehicle (the robot and task
family). No expansion is defined in the codebase; treated as a proper noun.
See [command-and-task.md](command-and-task.md).

**Asymmetric critic** — The critic (value + cost networks) consumes the full
106D input (`o_t` + `z` + raw `p_t`), while the actor only ever sees `o_t` + `z`
(78D) — the critic has privileged information the actor does not. See
[main-network-architecture.md](main-network-architecture.md) §1, §2.4.

**Attitude-only task** — The default task's goal is roll/pitch attitude plus a
yaw-**rate** command; there is no linear-velocity command or tracking (no DVL
on the real robot). See [command-and-task.md](command-and-task.md).

**BlueROV** — A separate task suite (5 registered tasks, `Isaac-BlueROV-*-Direct-v0`)
in `marinelab/marinelab/tasks/bluerov/`, distinct from the ALBC task family in
this repo.

**ConstraintTRPO** — The training algorithm: Trust Region Policy Optimization
with an IPO interior-point log-barrier folded into the surrogate objective, a
pure-KL trust region (barrier curvature excluded from the Fisher), and an
asymmetric critic. See [constraints.md](constraints.md) §1.

**control_delay_steps** — A `(low, high)` randomization range (config field on
`envs/main`) for per-env action-delay buffering; `(0, 0)` disables the delay.
One of the 28 `p_t` components (normalized delay, 0 when off). See
[observation-space.md](observation-space.md) §1.

**CV (coefficient of variation)** — `ss_error_std / ss_error`, used to detect
env-to-env spread that a mean alone hides; CV > 100% means the spread exceeds
the mean (heavy-tail-prone). Defined in `.claude/rules/03-analysis-quality.md`
("Env-to-Env Variance Analysis").

**DORAEMON** — "Domain Randomization via Entropy Maximization" (Tiboni et al.,
ICLR 2024): the adaptive Beta-distribution curriculum that schedules the
17-parameter physics-DR surface. Engine in
`marinelab/marinelab/algorithms/doraemon.py`. See
[domain-randomization-and-doraemon.md](domain-randomization-and-doraemon.md).

**DR (domain randomization)** — Randomizing physics/actuator parameters across
envs so the policy generalizes sim-to-real. This codebase has 4 evaluation
levels — `none` / `soft` / `medium` / `hard` — swept by `eval.py static`
(`analysis/dr_config.py`, `analysis/eval.py`); training itself uses the
DORAEMON-curriculum HARD range plus a disjoint uniform-only surface. See
[domain-randomization-and-doraemon.md](domain-randomization-and-doraemon.md).

**Encoder / latent z** — A privileged-information encoder: `p_t` (28D) is
compressed (static min-max normalize, MLP, elu, LayerNorm, softsign) into a 9D
latent `z`, which the actor consumes instead of raw `p_t`. See
[main-network-architecture.md](main-network-architecture.md) §1, §3.

**Heavy-tail** — A per-env outlier failure mode (extreme envs, e.g. peak
attitude error > 20 deg) that mean+std cannot detect on its own — distinct from
sample-mean divergence. Defined in `.claude/rules/03-analysis-quality.md`
("Heavy-tail vs Sample-mean Divergence").

**IPO** — Interior-Point Optimization: the log-barrier method that turns each
of the 10 cost-budget constraints into a smooth barrier term added to the TRPO
surrogate objective, rather than a Lagrangian dual or projection step. See
[constraints.md](constraints.md) §1.

**o_t (observation)** — The 69D actor observation: 20D current proprioception +
46D strided temporal history + 3D leaky error integral. Deliberately excludes
measured linear velocity (no DVL on the real robot). See
[observation-space.md](observation-space.md) §2.

**p_t (privileged observation)** — The 28D simulator-only ground-truth vector
(25 DR-backed physics scalars + 3D measured body linear velocity) fed only to
the encoder and the critic, never directly to the actor. See
[observation-space.md](observation-space.md) §1, §2.2.

**run_id / group / campaign** — `run_id` is `make_run_id()`'s
`<task_short>[_<tag>]_<ts>` output (label-before-date, timestamp trailing);
`group` is the `--run_group` campaign layer created by `train.py` at launch
(`experiments/rsl_rl/<exp>/<group>/<run_id>/`); one campaign (group) maps to
one wandb project. See `.claude/rules/02-operations.md` and
`constrained_albc/analysis/paths.py`.

**ss_error / ss_jitter** — Steady-state metrics computed over the last 50% of
an attitude segment in `eval.py static`: `ss_error` is the per-env-then-mean
tracking error (DC offset); `ss_jitter` is the per-env temporal std then
mean-across-envs (AC oscillation) — a low `ss_error` with rising `ss_jitter`
signals policy oscillation, not tracking failure. See
`constrained_albc/analysis/_eval_dr/metrics.py` and
`.claude/rules/03-analysis-quality.md`.

**step_dt vs physics_dt / decimation** — `physics_dt` is the raw PhysX step
(`sim.dt = 0.005s`); `decimation = 4` means one control step advances physics 4
times, so `step_dt = physics_dt * decimation = 0.02s` (50 Hz control). Actuator
dynamics (e.g. the thruster first-order lag) must advance with `step_dt`, not
`physics_dt` — a past bug used the wrong one. See `envs/main/config.py` and
`envs/main/albc_env.py` (`apply_dynamics` call site).

**TAM (thruster allocation matrix)** — The fixed 6x6 matrix mapping 6
per-thruster forces to a body-frame 6-DOF wrench
(`einsum("ij,nj->ni", allocation_matrix, thrust_magnitude)`), taken from the
ALBC ROS control package. See [action-pipeline.md](action-pipeline.md) §5.

**TCN/GRU student** — The distillation student encoder: a TCN (windowed
temporal-convolution) or GRU (recurrent) network trained to reproduce the
teacher's latent `z` (`l_hat`) from observation history alone, without access
to `p_t`. See `constrained_albc/envs/main/student/`.

**Teacher-student distillation** — Training the TCN/GRU student encoder
(supervised, frozen teacher actor) to approximate the privileged-encoder latent
`z` from history the real robot actually has, so the deployed policy does not
need `p_t` at inference. See `constrained_albc/envs/main/student/runner.py`.

**TDC** — Time Delay Control: a model-based control law (not RL) implemented
as a separate task variant (`Isaac-ConstrainedALBC-TDC-v0`, `envs/tdc/`), used
as a classical-control comparison baseline. See
`docs/explanation/tdc-control-law.md`.

**TRPO** — Trust Region Policy Optimization: the base natural-gradient policy
update (KL-constrained trust region) that `ConstraintTRPO` extends with the IPO
barrier. See [constraints.md](constraints.md) §1.

**UUV/UVMS** — `UUV`: this workspace's own term for the underwater
vehicle-manipulator system under study (`/workspace/CLAUDE.md` §1). `UVMS`
(underwater vehicle-manipulator system) is the term used in the field
literature this repo cites (`docs/explanation/tdc-literature.md`) — same
concept, literature-standard name.
