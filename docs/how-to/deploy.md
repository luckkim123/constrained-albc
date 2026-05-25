# Full-DOF ALBC Sim-to-Real Deployment Guide

## Purpose

이 문서는 `constrained_full_albc` 프로젝트에서 훈련된 ConstraintTRPO + Asymmetric Encoder 정책을 실제 UUV (Hero Agent 기반) 하드웨어로 배포하기 위한 절차를 정의한다. 주 대상 task는 `Isaac-FullDOF-TRPO-v0`.

이 가이드는 다음 실험 결과를 근거로 한다:
- `r13a_layernorm` 실험 (2026-04-21): `EmpiricalNormalization` → `LayerNorm` 교체 시 reward -33%, yaw ss_error +1975%. **Actor obs-input LayerNorm은 채널 간 상대 scale을 파괴하므로 배포용 normalizer로 사용 금지**.
- 관련 문헌 (Engstrom-Ilyas 2020, Andrychowicz 2020, HORA, RMA, RLPD): running stats + freeze가 RL sim-to-real의 standard practice.

## Architecture Overview

배포 대상 구성요소:
- **Actor network**: `ActorCriticEncoder.actor` — MLP [256, 128, 64], input = 87D policy obs (hist_len=3 기준), output = 8D action (mean).
- **Actor obs normalizer**: `EmpiricalNormalization(87)` — running `_mean`/`_std`/`count` buffers. 훈련 종료 시 freeze.
- **Encoder**: **배포 제외**. 훈련 중 teacher가 privileged obs (23D)로 context 제공. Student/adapter가 부재하므로 배포 actor는 encoder latent에 의존하지 않음 (현재 r13a 구성에서는 encoder z가 actor input에 concat되지만, 배포 시 teacher privileged obs가 없으므로 대체 필요 — 자세한 내용은 Stage 2 참고).
- **Critic**: **배포 제외**. 훈련용.

**중요**: 현재 `constrained_full_albc`의 actor는 encoder가 제공하는 latent z (9D) 없이는 동작하지 않는 구조일 가능성이 있다. Deploy 전에 `actor_critic_encoder.py`의 `actor_obs` 구성을 반드시 확인하고, z가 필요하면:
(a) 실기에서 privileged obs 근사가 불가하므로 student/adapter module을 별도 훈련해야 한다 (HORA/RMA Phase 2 방식), 또는
(b) z가 actor input에서 제외되는 ablation run이 선행되어야 한다.

## Deployment Procedure

### Stage 1. Model Export

훈련 종료 직후, 체크포인트에서 배포용 bundle 추출.

```python
import torch

# 훈련 종료 시점 (scripts/reinforcement_learning/rsl_rl/train.py 수정 또는 별도 스크립트)
runner.alg.actor_critic.eval()   # EmpiricalNormalization.update() 비활성화

export_bundle = {
    "state_dict": runner.alg.actor_critic.state_dict(),
    "obs_spec": {
        "dim": 87,
        "hist_len": 3,
        "hist_stride": 3,
        "hist_action_len": 2,
        "channel_layout": [
            # config.py:_OBS_NOISE_STD 주석의 순서를 그대로 복사
            ("cmd_lin", 3), ("cmd_ang", 3),
            ("euler", 3), ("ang_vel", 3), ("lin_vel", 3),
            ("joint_pos", 2), ("joint_vel", 2), ("manip", 1),
            ("thruster_state", 6),
            ("joint_hist", 12),      # (jp_err 2 + jv 2) * 3
            ("body_hist", 27),       # (lv_err 3 + ang_err 3 + rpy 3) * 3
            ("action_hist", 16),     # 8 * 2
            ("integral", 6),
        ],
    },
    "action_spec": {"dim": 8, "range": [-1.0, 1.0], "control_rate_hz": 50},
    "dr_train_range": {  # 실기 실측과 비교용
        "payload_mass": (0.5, 2.5),
        "payload_cog_xy": 0.08,
        "buoyancy_force": (85, 95),
        "ocean_current_max": (0.5, 0.5, 0.25),
        # ... config.randomization의 HardDR 값 복사
    },
    "git_sha": subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip(),
    "checkpoint_path": resume_path,
}
torch.save(export_bundle, "deploy_model.pt")
```

### Stage 1 Verification

배포 bundle 검증:

```python
# 1. EmpNorm이 실제로 학습됐는지 확인
em = bundle["state_dict"]["actor_obs_normalizer._mean"]
assert em.abs().sum() > 0.01, "EmpNorm _mean is zero - not updated during training"

es = bundle["state_dict"]["actor_obs_normalizer._std"]
assert es.min() > 0.1 and es.max() < 100, "EmpNorm _std out of expected range"
assert (es == 1.0).sum() < 5, "EmpNorm _std mostly unchanged - update not fired"

# 2. state_dict에 policy/encoder/normalizer 모든 buffer 포함 확인
assert "actor_obs_normalizer._mean" in bundle["state_dict"]
assert "actor_obs_normalizer._std" in bundle["state_dict"]
assert "actor_obs_normalizer.count" in bundle["state_dict"]
```

분석 도구: `scripts/analysis/encoder_tools.py debug`로 per-channel `_mean`/`_std` 수치 확인. 극단적 값 (e.g., `_std < 0.01` 또는 `> 10`)이 있는 채널은 해당 obs dim이 거의 상수거나 발산 — 훈련 문제 의심.

### Stage 2. Real-Robot Obs Pipeline

**Sim-real 실패의 95%가 이 단계에서 발생**. `albc_env._get_observations()`와 **완전히 동일한** 87D 벡터를 실기에서 재구성해야 한다.

#### Checklist — Obs 재현 정확성

| 항목 | 확인 |
|------|------|
| 채널 순서 | `obs_spec.channel_layout`과 1:1 일치 |
| Body-frame vs World-frame | `ang_vel`, `lin_vel`은 body-frame (config.py 참고) |
| Quaternion → Euler 변환 | `euler_xyz_from_quat` 규약 (roll→pitch→yaw) |
| Angle wrapping | `euler` 범위 [-π, π] |
| Unit | joint_pos rad, joint_vel rad/s, lin_vel m/s, ang_vel rad/s |
| Command scaling | cmd_lin, cmd_ang은 훈련과 동일 정규화 범위 (`config.cmd_lin_max`, `cmd_ang_max` 확인) |
| Joint direction convention | 로봇 MDH 규약 vs sim URDF 규약 부호 일치 |
| Thruster state 정의 | Sim thruster model output (`self._thruster.state.abs()`) 과 실기 ESC feedback의 단위 일치 |
| History ring buffer | hist_stride=3 (3 physics step마다 샘플), hist_len=3 (최근 3 샘플 보관) |
| Action history 순서 | 최신이 앞/뒤 어느 쪽인지 config 구현 확인 |
| Integral error | episode reset 시 0, `_bias_ema` decay 계수 동일 |
| Control rate | 50Hz (control_decimation=4 × physics_dt=0.005) |

#### 권고: Shared Obs Construction Code

실기 제어 코드가 sim과 별도 구현이면 drift 발생 확률 급증. `albc_env._build_obs()` 로직을 **Isaac Sim에 의존하지 않는 유틸리티 함수**로 분리하여 실기에도 같은 함수를 import하는 구조 권고.

```
source/isaaclab_tasks/.../constrained_full_albc/obs_builder.py  (신설)
  def build_obs_vector(
      proprio: ProprioState,     # 실기/sim 공통 dataclass
      history: HistoryBuffer,    # ring buffer (hist_len x per-step features)
      commands: CommandState,    # cmd_lin, cmd_ang
      integral: torch.Tensor,    # 6D
  ) -> torch.Tensor:             # (batch, 87)
      ...
```

이 함수를 sim 측(`albc_env._get_observations()`)과 실기 ROS node에서 공유.

### Stage 3. EmpNorm Offline Recalibration

Sim 학습 stats와 실기 분포 차이가 크면 policy 입력이 왜곡된다. 배포 직전 실기에서 calibration data 수집 후 `_mean`/`_std` 재계산.

#### Procedure

1. 로봇을 **safe idle mode** 진입 (중립 thrust, arm 홀드). Tether 또는 얕은 수조.
2. **Zero-command**: cmd_lin = 0, cmd_ang = 0 유지.
3. **약한 외란**: operator가 수조에서 약한 current 주거나 로봇을 손으로 살짝 밀기 (0.1 m/s 이하). Sim DR이 커버하는 범위 내.
4. **Obs 수집**: 180초 × 50Hz = 9000 samples, policy는 **실행하지 않고** obs만 기록.
5. **Stats 재계산 + overwrite**:

```python
import torch

real_obs = torch.tensor(collected_obs_batch)  # (9000, 87)

sim_mean = model.actor_obs_normalizer._mean.clone()
sim_std = model.actor_obs_normalizer._std.clone()

real_mean = real_obs.mean(dim=0, keepdim=True).unsqueeze(0)
real_std = real_obs.std(dim=0, keepdim=True).unsqueeze(0)

# Drift 분석 — 채널별 비율 확인
ratio_mean = (real_mean - sim_mean).abs() / (sim_std + 1e-3)
ratio_std = real_std / sim_std
print("Channels with |real_mean - sim_mean| > 2 sim_std:", (ratio_mean > 2).sum().item())
print("Channels with real_std / sim_std > 3:", (ratio_std > 3).sum().item())

# 허용 기준: sim ↔ real std 비율이 0.3 ~ 3 사이여야 DR range가 실기 포함한다고 판단
if (ratio_std < 0.3).any() or (ratio_std > 3).any():
    raise RuntimeError("DR range insufficient — retrain with wider DR before deploy")

# Overwrite
model.actor_obs_normalizer._mean.copy_(real_mean)
model.actor_obs_normalizer._std.copy_(real_std)
model.actor_obs_normalizer._var.copy_(real_std ** 2)
# count는 그대로 두어도 무방 (eval 모드면 update 안 됨)
```

#### Acceptance Criteria

- 각 채널별 `|real_mean - sim_mean| < 2 * sim_std`
- `0.3 < real_std / sim_std < 3.0`
- 채널 80% 이상이 위 조건 충족

조건 미달 채널이 있으면 해당 채널 sensor calibration 또는 DR range 재설계 필요.

참고: `stable-baselines3`의 `VecNormalize.load_running_average()`가 동일 패턴.

### Stage 4. Safety Layer

정책 출력과 obs 파이프라인에 다층 안전 장치.

#### Obs Safety

```python
# Normalization 후 clipping (sensor dropout/outlier 방어)
normalized = (raw_obs - mean) / (std + eps)
normalized = torch.clamp(normalized, -5.0, 5.0)

# Stale obs detection
if time.time() - last_obs_ts > 0.1:  # 100ms 초과
    return neutral_action
```

#### Action Safety

```python
# Action rate limit (sim에서 허용된 최대 action rate의 70%)
ACTION_RATE_MAX = 0.5   # per 20ms step (sim rate limit 기준)
action = policy(normalized_obs).mean  # stochastic 아님, eval mode
action = torch.clamp(action, -1.0, 1.0)
delta = action - prev_action
delta = torch.clamp(delta, -ACTION_RATE_MAX, ACTION_RATE_MAX)
action = prev_action + delta

# Low-pass filter (jitter 억제)
action = 0.85 * action + 0.15 * prev_action
```

#### Watchdog

```python
# 5 step 연속 |action| > 0.95 → thruster saturation 지속 → unsafe
saturation_count = saturation_count + 1 if action.abs().max() > 0.95 else 0
if saturation_count > 5:
    enter_safe_mode()  # 중립 thrust, arm hold
```

#### DR Limit Monitor

실기 측정 환경 parameter (payload mass, buoyancy 등)가 sim DR range 밖이면 human operator에 경고. 사용자가 명시적 ack하기 전까지 mission 진행 중단.

### Stage 5. Staged Rollout

단계별 검증. 각 단계의 acceptance criteria를 통과해야 다음 단계 진행.

| Stage | 환경 | Cmd Envelope | Thruster 상한 | Duration | Pass Criteria |
|-------|------|--------------|---------------|----------|---------------|
| 5.1 Tethered hover | 수조, tether 고정 | cmd = 0 | 50% | 30 min | pos drift < 0.1 m, att drift < 5° (free floating) |
| 5.2 Shallow tank | 수조, tether 유지 | att setpoint, lv = 0.1 m/s | 70% | 1 h | sim eval_dr soft level과 trajectory RMSE < 2x |
| 5.3 Progressive cmd | 수조 | lv 0.1→0.5 m/s, yaw_rate 0→0.5 rad/s 단계적 | 90% | 2 h | 각 cmd level에서 ss_error가 sim medium DR level과 비슷 |
| 5.4 Open water | 실해역 | Mission cmd | 100% | Mission별 | Pre-mission safety checklist 통과 |

각 stage에서 **실기 trajectory 로그**를 sim에 replay (`scripts/analysis/replay_realworld.py` 신설 필요) — sim과 실기 응답 차이가 sim2real residual의 정량 지표.

### Stage 5 Pre-flight Checklist (Stage 5.4 Open Water)

- [ ] `deploy_model.pt` git_sha가 최신 training run과 일치
- [ ] `obs_spec.channel_layout` 실기 코드와 diff 확인
- [ ] EmpNorm stats가 Stage 3에서 recalibrate 완료
- [ ] 배터리 > 80%
- [ ] Tether/surface buoy 준비
- [ ] GCS 통신 3중화 확인
- [ ] E-stop 접근 가능
- [ ] Safety watchdog 임계값 설정 ack
- [ ] DR limit monitor 활성화
- [ ] 로깅: raw_obs, normalized_obs, action, timestamp, sim_time_lag 전체 기록

## Troubleshooting

### Symptom: 실기에서 oscillation / jitter

| 원인 | 진단 | 대처 |
|------|------|------|
| EmpNorm stats 불일치 | channel별 `real_std / sim_std` 확인 | Stage 3 recalibration 재수행 |
| Control rate mismatch | 실기 loop이 50Hz 아닌지 측정 | dt 정합성 확인 |
| Action low-pass 부족 | action rate 측정 | filter α 조정 (0.8 → 0.9) |
| Sim DR이 실기 포함 안 함 | DR Limit Monitor 경고 | DR range 넓혀 재훈련 |

### Symptom: 실기에서 pos drift 지속적

| 원인 | 진단 | 대처 |
|------|------|------|
| Integral saturation | integral obs dim 값 확인 | integral clamp 추가 |
| cmd scaling 오류 | sim cmd와 실기 cmd 같은 범위인지 확인 | cmd normalization 재정합 |
| Buoyancy mismatch | 실기 측정 buoyancy vs sim 기본값 | payload 조절 또는 DR 재훈련 |

### Symptom: 특정 축만 악화 (e.g., yaw)

문헌상 LayerNorm 교체 실험에서 yaw가 가장 민감 — 해당 축 obs channel (ang_vel[2], ang_err_hist[2 of 9]) 의 scale/부호 재검토 우선.

## References

- Engstrom L, Ilyas A et al. 2020. "Implementation Matters in Deep Policy Gradients: A Case Study on PPO and TRPO". arxiv:2005.12729.
- Andrychowicz M et al. 2020. "What Matters In On-Policy RL? A Large-Scale Empirical Study". arxiv:2006.05990.
- Kumar A, Fu Z, Pathak D, Malik J. 2021. "RMA: Rapid Motor Adaptation for Legged Robots". RSS. arxiv:2107.04034.
- Qi H, Kumar A et al. 2022. "In-Hand Object Rotation via Rapid Motor Adaptation". CoRL. arxiv:2210.04887.
- Ball P, Smith L, Kostrikov I, Levine S. 2023. "Efficient Online Reinforcement Learning with Offline Data (RLPD)". ICML. arxiv:2302.02948.
- Chaffre T et al. 2025. "Sim-to-real transfer of adaptive control parameters for AUV stabilisation under current disturbance". IJRR.
- Muratore F et al. 2022. "Robot Learning From Randomized Simulations: A Review". Frontiers in Robotics and AI.
- Coholich J. "A Bag of Tricks for Deep Reinforcement Learning". (practitioner guide)

## Related Internal Docs

- [system-overview.md](../explanation/system-overview.md) — 시스템 전반 구성 + 알고리즘
- [reward-design.md](../explanation/reward-design.md) — reward 구조
- [experiments-archive.md](../reference/experiments-archive.md) — 관련 실험 기록

## Changelog

- 2026-04-21: 초안 작성. r13a_layernorm (2026-04-21) 실험 실패 결과와 문헌 조사 결과 반영.
