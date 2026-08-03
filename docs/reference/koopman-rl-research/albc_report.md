# Constrained-ALBC Teacher/Student Input Interface — Exact Map

Repo: `/workspace/constrained-albc`. All claims below carry `file:line` anchors verified by direct read (2026-08-03). No design proposals — facts and code quotes only.

## 1. Policy observation o_t — declared 69D, runtime 72D

**Declared width**: `constrained_albc/envs/main/config.py:431` `observation_space: int = 69`.

**Runtime width is 72D**, not 69D: `use_bias_ema_obs: bool = True` is the *default* (`config.py:453`), and `apply_bias_ema_obs()` (`config.py:683-724`) bumps `cfg.observation_space += 3` (`config.py:713`) at `ALBCEnv.__init__` time, before `super().__init__()` builds the gym space (`albc_env.py:112`, comment `albc_env.py:108-112`). The 69D figure in `config.py:431` is deliberately the *pre-bump* width (`config.py:702-707` raises if it isn't exactly 69 when the materializer runs). Confirmed independently by omx wiki (`attitude_only_ablation_arms_registered_policy_obs_dim_sync_must_.md`, quoted in §6): *"`envs/main` is 72D, not the 69D its cfg source declares... Read the checkpoint instead: `actor.0.weight` in_features is obs + latent (81 = 72 + 9; a stale 69 would give 78)."*

Assembly, in order, from `ALBCEnv._get_observations` (`albc_env.py:1118-1178`):

| Segment | Dims | Source | Anchor |
|---|---|---|---|
| Current proprioception | 20D | `compute_policy_obs()` | `albc_env.py:1129`, def at `mdp/observations.py:42-86` |
| — Command | 3D `[roll_att_cmd, pitch_att_cmd, yaw_rate_cmd]` | `env._ang_cmd` | `mdp/observations.py:51-52,74` |
| — Body state | 6D euler(3) + ang_vel(3) | `env._euler_cache`, `robot.data.root_ang_vel_b` | `mdp/observations.py:54-57,76-77` |
| — Arm state | 5D joint_pos(2) + joint_vel(2) + manipulability(1) | `robot.data.joint_pos/vel[albc_joint_ids]`, `env._manipulability` | `mdp/observations.py:58-61,79-81` |
| — Thruster state | 6D filtered ESC output m0-m5 | `env._thruster.state` | `mdp/observations.py:63-64,69,83` |
| Joint+body tracking history | 30D = 10D × `hist_len`(3) | `env._hist_buf[:,:,:10]` (joint_pos_error+joint_vel = 4D, ang_err+rpy = 6D, per `hist_feature_dim=18` layout `config.py:511-512`) | `albc_env.py:1133`, buf alloc `albc_env.py:358-361`, dims defined `config.py:507-512` |
| Action history | 16D = 8D × `hist_action_len`(2) | `env._hist_buf[:,-2:,10:]` (newest 2 of 3 stored steps) | `albc_env.py:1135` |
| Integral error | 3D `[roll, pitch, yaw_rate]` | `env._error_integral` (leaky, gated) | `albc_env.py:1141-1142`, updated `albc_env.py:1198-1218` |
| **Subtotal (declared 69D)** | **20+30+16+3 = 69** | | |
| Bias-EMA (default ON) | 3D `[roll, pitch, yaw_rate]` | `env._bias_ema` (EMA of tracking error, updated only if `reward.k_bias != 0`) | append `albc_env.py:1147-1148`; update `albc_env.py:1220-1232`; materializer `config.py:683-724` |
| **Runtime total** | **72D** | | assert `albc_env.py:1172-1175` |

After assembly, two *additive, independently-toggleable* noise layers are applied via `faults.apply_sensor_noise` (both no-ops/identity by default): a per-env sensor-fault noise layer (`albc_env.py:1150-1156`) and a DORAEMON-curriculum extra-noise layer (`albc_env.py:1158-1163`). This is on top of the always-on `NoiseModelWithAdditiveBiasCfg` (`config.py:631-634`, std table `_OBS_NOISE_STD` `config.py:304-321`, per-episode bias `_OBS_BIAS_MIN/MAX` `config.py:324-343`) which isaaclab's `DirectRLEnv` noise pipeline applies before these two.

**Command dims**: 3D, part of the 20D current-proprio block above — `att_cmd_rp_range = (-π/6, π/6)` (`config.py:519`), `yaw_rate_cmd_range = (-0.5, 0.5)` (`config.py:521`). No separate command tensor is fed to the network outside `o_t`.

**Action dim**: `action_space: int = 8` (`config.py:430`, comment: 2D arm delta + 6D thruster).

**Optional obs4 side-channel (off by default)**: `use_student_extra_obs: bool = False` (`config.py:663`) — when on, `compute_student_extra_obs()` (`mdp/observations.py:224-282`) computes 4D `[IMU specific-force xyz (3D), pressure-derived heave rate (1D)]` at a zero-order-hold of `extra_obs_hold_steps=2` ticks (25 Hz vs 50 Hz control tick, `config.py:669-680`), published as `observations["student_extra"]` (`albc_env.py:1170-1171`, key defined `models.py:20`) — **not** concatenated into `policy_obs` in the current generation ("gen-1"); the frozen teacher actor never sees it (`mdp/observations.py:236-237`).

## 2. Privileged obs p_t — 28D (34D with Arm-B fault extension)

`state_space: int = 28` (`config.py:435`). Assembled by `compute_privileged_obs()` (`mdp/observations.py:89-204`), doc-comment layout `mdp/observations.py:108-139`, concat body `mdp/observations.py:155-191`:

| Block | Dims (index) | Content |
|---|---|---|
| Hydrodynamics | 7D `[0:7]` | volume(1) + CoG xyz(3) + CoB xyz(3) |
| Dynamic response | 3D `[7:10]` | quad-damping-roll(1) + body_mass(1) + added_mass_surge(1) |
| Payload | 4D `[10:14]` | payload_mass(1) + CoG offset xyz(3) |
| Actuator | 4D `[14:18]` | joint stiffness Kp, damping Kd, thrust coeff, time-constant-up |
| Environment | 4D `[18:22]` | water density(1) + ocean-current velocity xyz(3) |
| Buoy | 2D `[22:24]` | buoy volume + buoy body mass |
| Latency | 1D `[24]` | normalized control-action delay steps |
| Measured velocity | 3D `[25:28]` | `root_lin_vel_b` (u,v,w) — critic/encoder only, never in `o_t` (no DVL on real robot) |
| *Optional Arm-B* | *6D `[28:34]`* | *true per-thruster health, only when `cfg.use_privileged_fault_obs=True` (default `False`, `config.py:583`)* — `mdp/observations.py:193-202`, materializer `apply_privileged_fault_obs` `config.py:727-741` |

## 3. Teacher normalization — three independent normalizers, each gated

From `_core/encoder/actor_critic_encoder.py` docstring (`:8-34`) and code:

1. **Actor input (`o_t` only)**: `EmpiricalNormalization(policy_obs_dim)` when `actor_obs_normalization=True` (production default, `agents/rsl_rl_ppo_cfg.py:143`), applied only to `o_t`, not to `z` — `actor_critic_encoder.py:179-184, 258`. `z` is deliberately left un-normalized ("`z` is kept raw since softsign already bounds it to (-1, 1)", `actor_critic_encoder.py:34,252-254`).
2. **Encoder input (`p_t`)**: two mutually exclusive modes selected by whether `encoder_obs_lower/upper` are supplied:
   - **Static min-max** (production default): `(2*p_t - (upper+lower)) / (upper-lower) → [-1,1]`, deterministic, no running stats — `actor_critic_encoder.py:140-158,214-216`. Bounds are DR-range-derived per-dimension (`agents/rsl_rl_ppo_cfg.py:177-178`, `_PRIV_OBS_LOWER/_PRIV_OBS_UPPER`), overridden at build time with the live DR-derived bounds (comment `agents/rsl_rl_ppo_cfg.py:41`).
   - **EmpiricalNormalization** (legacy, `encoder_obs_normalization=True`): flagged in the class docstring as causing "z drift → KL spike" (`actor_critic_encoder.py:30`); production cfg sets `encoder_obs_normalization: bool = False` (`agents/rsl_rl_ppo_cfg.py:155`).
3. **Critic input**: `EmpiricalNormalization(num_critic_obs)` gated by `critic_obs_normalization` — production default `False` (`agents/rsl_rl_ppo_cfg.py:144`), so the critic sees raw `cat([o_t, z, p_t])` — `_policy_base.py:82-84,145,152`.

Production teacher geometry (`agents/rsl_rl_ppo_cfg.py:138-181`, `_ALBCPolicyCfg` docstring `:165-169`): `encoder_latent_dim=9`, `encoder_activation="elu"`, `critic_uses_z=True`, `encoder_output_norm=True` (LayerNorm before softsign). Declared: Encoder `p_t(28D)→static_minmax→MLP[256,128,64]→LN→softsign→z(9D)`; Actor `cat([o_t(69D declared), z(9D)])=78D→MLP[256,128,64]→8D`; Critic `cat([o_t(69D), z(9D), p_t(28D)])=106D→MLP[512,256,128]→1D`. **At the actual runtime obs width these become 81D actor input / 109D critic input** (72+9, 72+9+28) — per the wiki correction quoted in §1/§6.

## 4. Encoder — exact wiring (`_core/encoder/actor_critic_encoder.py`)

`_encode()` (`:209-220`):
```
p_t = obs[self._privileged_key]                    # 28D (or subset via _enc_obs_indices)
p_t = static_minmax(p_t)  OR  EmpiricalNorm(p_t)    # per §3 mode 2
z = softsign( LayerNorm_or_Identity( MLP[256,128,64,elu](p_t) ) )   # -> 9D
```
Input is **privileged obs `p_t` only** — the encoder never receives `o_t` or proprio history in the shipped architecture. (An unimplemented idea to also feed `o_t` into the encoder exists as an open wiki lead, see §6.) `z` joins the actor via `_get_actor_obs()` (`:249-259`): `torch.cat([EmpiricalNorm(o_t), z_raw], dim=-1)`. `z` joins the critic via `_get_critic_obs()` (`:261-271`): `cat([o_t, z(if critic_uses_z), p_t])`.

## 5. Student — exact wiring (`_core/student/`)

**Input to the student encoder is `o_t` (policy obs), never `p_t`.** The student distills the encoder's *output* (z), not its input mapping — student code never references privileged obs except via `StudentCfg.privileged_dim` (`student/config.py:46`), which exists purely for teacher-geometry bookkeeping (obs-dim consistency check, `student/runner.py:88-97`).

- **Normalization**: the student reuses the *teacher's frozen* `actor_obs_normalizer` instance directly — `self.obs_normalizer = self.teacher.policy.actor_obs_normalizer` (`student/runner.py:106`) — so `o_t` is normalized identically for teacher and student before either sees it (`student/teacher.py:182-184`, `normalize_obs`).
- **Single input-assembly point**: `student_input(obs_n, extra, scale)` (`student/models.py:23-38`) — `torch.cat([obs_n, extra/scale], dim=-1)` when `extra_obs_dim>0`, else `obs_n` unchanged. Every one of 4 call sites funnels through this one function: DAgger collection (`runner.py:269-273`), TCN loss (`runner.py:298-300`), GRU loss (`runner.py:313-316`), end-of-rollout hidden recompute (`runner.py:434-442`). The docstring explicitly names the incident this guards against: a duplicated inline copy (commit `38d979e`) "silently invalidated every in-loop verdict for two months" (`student/models.py:26-32`).
- **`extra` transport**: the obs-dict key is `STUDENT_EXTRA_OBS_KEY = "student_extra"` (`student/models.py:20`), populated by the env per §1 and read via `obs_td.get(STUDENT_EXTRA_OBS_KEY)` (`student/runner.py:368`); scale is `extra_obs_scale = (10.0, 10.0, 10.0, 1.0)` (`student/config.py:78`, divides before concat — "static... so the board runtime can replicate normalization from constants").
- **TCN** (`StudentEncoderTCN`, `student/models.py:60-109`): input window `(B, H=tcn_history, D=policy_obs_dim)`; `tcn_history=9` (`student/config.py:53`, "H=9 mirrors teacher's embedded history: stride=3 × 3 steps = 9 physical steps"); per-step channel transform `Linear(policy_obs_dim→32)+ELU` then `Conv1d` stack `channels=(64,128,128)` kernels `(3,3,3)` strides `(1,1,1)`, head `Linear→ELU→LayerNorm→Linear(→9)`, output `softsign`. History is built lazily from a flat ring buffer with gather (`student/collector.py:44,127-159`) for training, and from a separate persistent `collect_ring` (`(num_envs, tcn_history, policy_obs_dim)`, `student/runner.py:152-154`) during DAgger on-policy rollout collection — this is a *student-owned* ring, distinct from the env's own `_hist_buf` used to build `o_t`'s own 46D history block in §1.
- **GRU** (`StudentEncoderGRU`, `student/models.py:112-160`): `nn.GRU(input_size=policy_obs_dim+extra, hidden_size=128, num_layers=1, batch_first=True)` (`student/config.py:61-62`), streaming — `forward(obs_seq (B,T,D), hidden)` returns `(l_hat (B,T,9), hidden_out)`; head is `128→64→9` (`gru_head_hidden=64`, `student/config.py:63-68`) with LayerNorm, or a shallow `Linear` fallback if `gru_head_hidden=0`; output `softsign`. `init_hidden` zeros `(num_layers, B, gru_hidden)` (`student/models.py:162-163`).
- **Supervision target**: `l_hat` (student) is regressed to `l_t` (teacher's `z`, recorded per-step during rollout via `self.teacher.act`), and `a_hat = teacher.actor_forward(normalize(o_t), l_hat)` is regressed to `a_t` — loss = `||a_hat-a_t||² + λ·||l_hat-l_t||²` (`student/runner.py:1-9, 293-326`). The teacher's actor MLP weights are frozen and reused verbatim for both losses (`student/teacher.py:186-197`, `actor_forward`).

## 6. omx wiki — verbatim query output + read summaries

Commands run per task 5 (all succeeded; omx present at `/usr/local/bin/omx`):

```
$ omx wiki query --root /workspace/constrained-albc "encoder latent"
{"n_matches": 89, "n_returned": 20, ...}
```
Top hits: `latent_dim_d4_collapses_at_none_dr...` (score 8), `teacher_encoder_0_dead_latent_dims...` (score 8), `experiment_idea_feed_o_t_into_the_encoder_alongside_p_t...` (score 8), `encoder_latent_z_dim_ablation_coupling_points...` (score 7).

```
$ omx wiki query --root /workspace/constrained-albc "system identification"
{"n_matches": 34, "n_returned": 20, ...}
```
Top hits are all about *physical-plant* system ID (TAM/hydro measurement campaigns — `actuator_hardware_identification_arm_xw540...`, `sim_hydro_nominal_is_analytical_not_measured...`, `stonefish_base_hull_effective_hydro_measured...`). **None concern Koopman theory, linear operator lifting, or "system identification" in the sense the user's proposal invokes** — the phrase in this codebase means empirical hardware/hydrodynamic calibration, not the encoder's function.

```
$ omx wiki query --root /workspace/constrained-albc "auxiliary loss encoder"
{"n_matches": 99, "n_returned": 20, ...}
```
Top hit `experiment_idea_feed_o_t_into_the_encoder_alongside_p_t...` (score 7) — its snippet: *"Rule 03 (No-Encoder-Auxiliary-Losses): this is an INPUT change, not an aux loss -- allowed. Do NOT pair it with a reconstruction/contrastive loss (that path failed: decoder ignores z, z collapses)."* This corroborates `.claude/rules/03-analysis-quality.md`'s "No Encoder Auxiliary Losses" rule (reconstruction loss failed empirically: "decoder ignores z, z collapses").

```
$ omx wiki query --root /workspace/constrained-albc "observability student"
{"n_matches": 85, "n_returned": 20, ...}
```
Top hits: `latent_dim_d4_collapses_at_none_dr...` (score 8), `closed_loop_latent_collapse_suspicion...` (score 6, status **resolved**), `e0_eval_latent_instrument_fix_38d979e...` (score 6, status **resolved**), `on_policy_dagger_correction_for_the_buoyfix_student.md` (score 6, status **resolved**).

**Read pages** (3 most relevant):

1. **`experiment_idea_feed_o_t_into_the_encoder_alongside_p_t_state_co.md`** (category: convention, confidence: medium, status: open/unstarted, created 2026-07-08) — Documents the *current, verified* architecture as encoder-input = `p_t` only (matches §4 above verbatim: *"`_encode` (:206-216) reads `obs[self._privileged_key]` (= p_t, 27D) -> static min-max norm -> MLP[256,128,64] elu -> LayerNorm -> softsign -> z(9)"*). Proposes (unimplemented) feeding `o_t` into the encoder alongside `p_t`, citing RMA (Kumar 2021) precedent for state-conditioned latents. Flags 4 concrete design tensions: (1) redundancy risk — actor already sees `o_t` directly, so encoder-side `o_t` may make `z` collapse into a re-encoding of `o_t` rather than carrying physics info; (2) normalization mismatch — `p_t` uses DR-derived static min-max bounds, `o_t` uses running-stat EmpiricalNorm, mixing them in one encoder input needs a deliberate two-normalizer design; (3) the existing `encoder_obs_indices` selection hook (`actor_critic_encoder.py:125-137`) assumes a single input tensor, so concatenating obs groups before selection is new work; (4) student distillation's target changes if `z` depends on `o_t`. **Directly relevant to the user's proposal (1)**: this wiki entry already identifies the collapse risk of feeding proprioceptive info into a component whose purpose is to isolate *privileged* (non-observable) information — the same risk applies to any input-space lift that mixes `o_t`-derived and `p_t`-derived features.

2. **`literature_map_how_rl_control_actually_handles_steady_state_erro.md`** (category: reference, confidence: high, status: resolved) — Cross-domain literature survey (5 parallel document-specialist agents, primary sources quoted). Directly states a literature ranking table: *"encoder + student distillation (disturbance-as-latent) | 1st (most mature) | NO precedent in UUV RL"*. Under "COULD NOT FIND EVIDENCE": *"RMA-style privileged-encoder disturbance-latent estimation in UUV/AUV RL: no precedent found. RMA (Kumar et al., arXiv:2107.04034) is legged-only... We are doing this and the marine literature is silent on it."* No mention anywhere in this survey of Koopman operator theory, lifting functions, or linear-observable representations as a mechanism for implicit system ID in this codebase's literature base.

3. **`attitude_only_ablation_arms_registered_policy_obs_dim_sync_must_.md`** (category: convention, confidence: high) — Confirms the registered NoEncoder ablation task exists and works (§7), and is the source of the "72D not 69D" runtime correction quoted in §1: *"`envs/main` is 72D, not the 69D its cfg source declares... A run's saved `params/agent.yaml` records `policy_obs_dim: 69` even though the network was built at 72... Read the checkpoint instead: `actor.0.weight` in_features is obs + latent (81 = 72 + 9; a stale 69 would give 78)."*

## 7. Registered ablation tasks (gym registrations, grep-verified)

`constrained_albc/envs/main/__init__.py:14-21,35-87`:

| Task ID | Arm | `policy.class_name` | Encoder? |
|---|---|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | default: encoder + ConstraintTRPO + IPO | `ALBCActorCriticEncoder` | yes |
| **`Isaac-ConstrainedALBC-NoEncoder-v0`** | **TRPO + IPO, no encoder** | `ALBCActorCriticAsymConstrained` | **no** |
| `Isaac-ConstrainedALBC-PPO-v0` | stock PPO + asymmetric critic | `ActorCritic` (stock rsl-rl) | no |
| `Isaac-ConstrainedALBC-TRPO-NoIPO-v0` | encoder + TRPO, IPO off | (encoder policy) | yes |
| `Isaac-ConstrainedALBC-PPO-Enc-v0` | encoder + PPO, IPO off | (encoder policy) | yes |

`Isaac-ConstrainedALBC-NoEncoder-v0` (`agents/rsl_rl_ppo_cfg.py:307-349`) is the directly relevant ablation for the user's proposal (2) (drop the encoder). Its docstring (`:311-315`) gives the exact architecture: `Actor: o_t(69D) -> MLP[256,128,64] -> 8D`; `Critic/Cost: cat([o_t(69D), p_t(28D)])=97D -> MLP[512,256,128]`. Note this is a *pure* no-encoder ablation (no DR-latent estimation at all, actor sees `o_t` raw) — it is not a Koopman-lifted variant; no task in this registry performs any input lifting/transform. `envs/full_dof/__init__.py:33-76` registers the legacy full-DOF equivalents (`Isaac-ConstrainedALBC-Full-{TRPO,NoEncoder,PPO,TRPO-NoIPO,PPO-Enc}-v0`).

## 8. Lift-insertion points and ordering constraints (facts only — no design recommendation)

Three architecturally separate points exist where a per-step `phi(x)` transform sits in today's forward path, each with its own binding constraint drawn directly from the code read above:

- **(a) Teacher actor**: input is `cat([actor_obs_normalizer(o_t), z])` (`actor_critic_encoder.py:256-259`). `actor_obs_normalizer` is a *stateful* `EmpiricalNormalization` whose running-mean/var buffer shape is read directly out of checkpoints to *infer* `policy_obs_dim` (`student/teacher.py:41-55`, `infer_teacher_geometry`, comment: *"load (actor.0.weight 256x78 vs 256x81, normalizer 1x69 vs 1x72), which is how [dim mismatches are caught]"*). Any transform changing `o_t`'s dimensionality changes this buffer's shape and is therefore checkpoint-incompatible with every existing teacher checkpoint (r13_A and later). `z` bypasses this normalizer entirely (kept raw, `:252-254`).
- **(b) Encoder**: input is `p_t` (28D, or an `encoder_obs_indices` subset, `:126-137`), normalized either by fixed per-dimension DR-derived min-max bounds (`:140-158,214-216`, bounds shape-checked against `encoder_input_dim` at `:145-149`) or by a (deprecated) `EmpiricalNormalization`. `teacher.py:41-55` also reads `encoder.0.weight.shape[1]` directly from the checkpoint to infer `privileged_dim` — so a `phi(p_t)` that changes `p_t`'s width breaks checkpoint loading the same way as (a), and one that keeps the width but reorders/mixes dimensions breaks the fixed per-dimension min-max bounds (each bound is tied to one physical DR parameter, `mdp/observations.py:108-139`).
- **(c) Student**: input is `o_t`, funneled exclusively through `student_input()` (`student/models.py:23-38`), normalized by the *teacher's own frozen* `actor_obs_normalizer` instance (`student/runner.py:106`) — i.e., whatever normalization/lift is applied to `o_t` for the teacher's actor path in (a) is implicitly shared with the student, since it is literally the same `nn.Module` object, not a copy. The student never touches `p_t` or the encoder's input path at all — it only ever targets the encoder's *output* `z`. The codebase carries an explicit warning against a second, inlined copy of this concat (`:26-32`, referencing the `38d979e` incident that "silently invalidated every in-loop verdict for two months").

Cross-cutting: `observation_space`/`state_space`/`policy_obs_dim`/`privileged_dim` are checked for consistency in at least 4 independent places (`albc_env.py:184-210` runtime assert, `student/runner.py:92-97` teacher-vs-env assert, `_core/runners/__init__.py` `sync_policy_obs_dim` per the wiki `attitude_only_ablation_arms_registered...` page, and the checkpoint-shape inference in `teacher.py:41-55`) — any dimensionality-changing transform inserted at (a)/(b)/(c) has to satisfy all four simultaneously or fails loudly at load/init time (not silently).