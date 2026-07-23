---
title: "Container cuDNN is cu13 against cu128 torch: every conv1d fails, student distillation is 70x slower with the workaround"
tags: ["environment", "cudnn", "student", "distillation", "infra"]
created: 2026-07-22T10:05:40.444434
updated: 2026-07-23T08:10:24.034283
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: needs-apply-before-retrain
blocked-on: "Image-level package change (replace nvidia-cudnn-cu13 with the cu12 build matching torch 2.7.0+cu128). Human-gated: modifies /isaac-sim site-packages. Workaround (cudnn disabled in scripts/train_student.py, commit 2888d49) keeps distillation CORRECT but ~70x slower. ALTERNATIVE 2026-07-23: DGX cuDNN probe PASSED (torch 2.9.0+cu130, cudnn 91300), so C4 distillation can be hosted there instead of waiting on the image fix -- human decision, does not close this lead."
---

# Container cuDNN is cu13 against cu128 torch: every conv1d fails, student distillation is 70x slower with the workaround

Any cuDNN conv in this container fails with CUDNN_STATUS_NOT_INITIALIZED, even on a
completely idle GPU with a 21 MB tensor. It is neither an OOM nor a GPU fault.

Evidence (2026-07-22, both RTX 4070 and RTX 4060, driver 575.57.08, both sm_89):
- plain CUDA matmul on the same device: OK
- conv1d with torch.backends.cudnn.enabled = False: OK
- conv1d with cuDNN enabled: CUDNN_STATUS_NOT_INITIALIZED
- CUDNN_LOGERR_DBG=1 names the cause exactly:
  "cudnnCreate(): Error: CUDNN_STATUS_NOT_INITIALIZED; Reason:
   cudaGetDeviceCount(&count) != cudaSuccess"

Root cause is a package mismatch in the image:
  torch                2.7.0+cu128   (CUDA 12.8)
  nvidia_cudnn_cu13    9.20.0.48     (CUDA 13)
  nvidia_cuda_runtime  13.0.96       (CUDA 13)
cuDNN's own CUDA-13 runtime cannot enumerate devices inside torch's CUDA-12.8
context. The cu13 packages are dated 2026-07-12.

Why it went unnoticed for ten days: the student TCN is the ONLY conv in this
codebase. Teachers are pure MLP, so every teacher run -- including the 5000-iteration
buoyfix anchor seeds -- is completely unaffected. The last successful distillation
(trpo_student_tcn_armA_260629_105521) predates the cu13 install.

Workaround in effect: scripts/train_student.py sets torch.backends.cudnn.enabled =
False (commit 2888d49). Correctness is NOT affected -- the native conv is what the
deployed numpy runtime mirrors, and deploy/golden.py already generates goldens on
CPU precisely because cuDNN conv differs by ~1e-4.

The cost is speed, and it is large. Measured time_train per iteration:
  0.243 s  legacy student 2026-06-29 (cuDNN working)
  ~17 s    2026-07-22 with cuDNN disabled     -> ~70x
time_collect is unchanged (0.519 s -> 0.60 s), confirming the whole penalty is in
the conv. A 1000-iteration distillation therefore takes ~4.9 h instead of ~13 min.

Budget consequence: treat every TCN/GRU student distillation as a ~5 h job until the
image is repaired, not the ~15 min the older runs suggest.

Repair and verification:
  replace nvidia-cudnn-cu13 with the cu12 build matching torch's CUDA 12.8, then
  python -c "import torch, torch.nn as nn; nn.Conv1d(32,64,3).cuda()(torch.randn(64,32,9,device='cuda'))"
  and delete the cudnn-disable line in scripts/train_student.py.

---

## Update (2026-07-23T08:10:24.034283)

## The DGX does not have this bug (2026-07-23 probe)

The DGX stand-down session ran the same conv1d check on the GB10 box and it passed:
torch 2.9.0+cu130, cudnn 91300, conv1d forward and backward with gradients, no
CUDNN_STATUS_NOT_INITIALIZED. So this is a workstation-image defect, not a property of
the codebase or of conv1d on this hardware class.

That opens a second way past the 70x slowdown, alongside the image fix: run student
distillation on the DGX instead. It is legitimate under machine isolation specifically
because distillation is supervised imitation from a FROZEN workstation teacher
checkpoint -- the teacher is the file, not the machine, so no cross-machine performance
term enters any campaign comparison (teacher-campaign-plan section 8, "Machine
allocation"). It is a human decision, and it does NOT close this lead: the workstation
image stays broken either way, which still costs every future conv1d workload here.

Evidence is a relayed report from the DGX session, not reproducible from the
workstation. Re-run the probe on DGX before committing a distillation block to it.

