#!/usr/bin/env bash
# OMX profile - training launch recipe. exp-loop (#6) QUEUES this as a
# 'pending approval' artifact; it is NEVER auto-fired (design D4/B8).
# Fill in your training command + GPU gate, then the human launches it.
set -euo pipefail

# GPU gate (example - adapt to your setup):
#   nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits

# Training command (placeholder - substitute your entrypoint; nothing machine-specific):
#   cd "$OMX_PROJECT_DIR" && python <your_train_entrypoint> --task "$OMX_TASK" ...
echo "launch.sh is a template; fill in your training command. exp-init never runs it."
