"""tb_final.py reducer check (G2, 2026-07-27).

Writes a tiny synthetic TB run, reduces it, and checks the last-window mean
plus the null contract for absent tags.

Run: /isaac-sim/python.sh -m pytest test_tb_final.py
(system python3: skipped -- no tensorboard writer there, which is the point of G2)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "tb_final.py"


def test_reduce_last_window_mean():
    torch_tb = pytest.importorskip("torch.utils.tensorboard")
    with tempfile.TemporaryDirectory() as td:
        w = torch_tb.SummaryWriter(td)
        for i in range(100):
            w.add_scalar("Train/mean_reward", float(i), i)
        w.close()
        r = subprocess.run(
            [sys.executable, str(SCRIPT), td, "--tags", "Train/mean_reward", "Missing/tag", "--window", "10"],
            capture_output=True, text=True, timeout=180,
        )
        assert r.returncode == 0, r.stderr[-500:]
        out = json.loads(r.stdout)[td]
        assert out["Train/mean_reward"] == pytest.approx(94.5)  # mean of 90..99
        assert out["Missing/tag"] is None
