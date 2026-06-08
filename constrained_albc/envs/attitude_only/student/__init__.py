"""Student policy package: TCN + GRU encoders distilled from r13_A teacher.

Exports:
    StudentCfg  -- training configuration
    StudentEncoderTCN, StudentEncoderGRU  -- encoder architectures
    FrozenTeacher  -- frozen teacher wrapper
    RolloutBuffer, collect_rollout  -- online data collection
    StudentRunner  -- supervised training loop
"""
