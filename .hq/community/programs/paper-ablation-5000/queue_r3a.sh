#!/bin/bash
# Queue the ten paper-ablation-5000 R3a-anchor runs as pending-launch artifacts (no training starts here).
# Run inside the container after anchor/r3a-5000 is committed. Gates acked per run: finding/264, 352, 441, 444.
# 2026-09-12 review re-queue: chain order ref first, chain md5 recorded, predicted outcomes corrected against the
# p3b curriculum_trajectory.json (fault_severity mean 0.0132 at it 1000, 0.023 at it 2000 -- not > 0.05).
set -eu
W=/workspace/constrained-albc-r3a
COMMIT=$(git -C "$W" rev-parse --short HEAD)
cd /workspace/constrained-albc
CHAIN=.hq/community/programs/paper-ablation-5000/launch_chain_r3a.sh
CHAIN_MD5=$(md5sum "$CHAIN" | cut -c1-8)
BASE="anchor/r3a-5000 @ $COMMIT (ea42375 + finding/441 #6/#7 + ATDC leak + N6 cfgs + N6b encoder-bounds fix) with marinelab worktree @ 8cc84a5 (velocity_limit_sim 3.1, pre-p5); PYTHONPATH=$W:/workspace/marinelab-r3a; 4096 envs, seed 30, 5000 it, run_group paper_ablation_r3a; chain launch_chain_r3a.sh md5 $CHAIN_MD5"
q(){ # run_id task variant position hours predicted
  omx queue-launch --run-id "$1" --proposal-id paper-ablation-5000 \
    --launch-delta "$BASE; task $2; as-run gate --variant $3" \
    --gpu-gate "GPU0 RTX 4070, chain position $4/10, about $5 h; GPU1 stays free for evals" \
    --predicted-outcome "$6" --cwd "$W" \
    --ack-gate finding/264 --ack-gate finding/352 --ack-gate finding/441 --ack-gate finding/444
}
q r3a5000_ref_full_s30      Isaac-ConstrainedALBC-TRPO-SimToReal-v0                 section5      1  6 "canary against p3b (same seed, same config): DORAEMON/mode reaches 0 by it 1000 (p3b -3,-2,0,0 at 250/500/750/1000), fault_severity mean near p3b 0.013 at it 1000 and 0.023 at it 2000, no nan; hard tier within p3b model_5000, which is scored beside it as a same-seed second realization"
q r3a5000_a6_ppoenc_s30     Isaac-ConstrainedALBC-PPO-Enc-SimToReal-v0              section5      2  4 "gate ok at it 0, no nan, completes 5000 it; whether PPO-Enc return clears lb 200 and opens the curriculum is the arm's property, not a pipeline check"
q r3a5000_n1_lagrangian_s30 Isaac-ConstrainedALBC-TRPO-Lagrangian-SimToReal-v0      section5      3  5 "completes 5000 it; if the finding/444 #2 cost-critic nan path fires, the chain kills the arm and that is the N1 row"
q r3a5000_n4_residual_s30   Isaac-ConstrainedALBC-Main-ResidualTDC-SimToReal-v0     section5      4  5 "completes 5000 it on a TDC base at default gains kp 48 / kd 14 (not the 8-R-3 retuned gains); curriculum opening unmeasured"
q r3a5000_noenc_s30         Isaac-ConstrainedALBC-NoEncoder-SimToReal-v0            section5      5  4 "completes 5000 it; hard-tier survival at or below ref (08-24 old-plant suite pattern, finding/031)"
q r3a5000_ppo_s30           Isaac-ConstrainedALBC-PPO-SimToReal-v0                  section5      6  3 "completes 5000 it; by median may match ref at hard (finding/395), mean below ref"
q r3a5000_noipo_s30         Isaac-ConstrainedALBC-TRPO-NoIPO-SimToReal-v0           section5      7  4 "completes 5000 it; more constraint violation than ref (cost readout: exam chain --save-extras, reference-constraint swap)"
q r3a5000_noboth_s30        Isaac-ConstrainedALBC-TRPO-NoIPO-NoEncoder-SimToReal-v0 section5      8  3 "completes 5000 it; more constraint violation than ref and noenc (cost readout: exam chain --save-extras, reference-constraint swap)"
# WITHDRAWN 2026-09-12 (operator: n6a/n6b 제외): q r3a5000_n6a_nodoraemon_s30 Isaac-ConstrainedALBC-TRPO-SimToReal-NoDoraemon-v0     n6-nodoraemon 9  7 "full static DR from it 0 (no curriculum): training return below ref through it 1000; none tier worse than ref"
# WITHDRAWN 2026-09-12 (operator: n6a/n6b 제외): q r3a5000_n6b_nodr_s30      Isaac-ConstrainedALBC-TRPO-SimToReal-NoDR-v0            n6-nodr       10 7 "nominal-point plant: highest training return of the chain, no nan (encoder bounds from section-5), worst medium/hard tier; must be scored under the ref task, not its own"
ls -d .hq/work/experiments/runs/r3a5000_*
