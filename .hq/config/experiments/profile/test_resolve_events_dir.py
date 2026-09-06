"""experiments-dir -> logs-dir resolution via the train/ symlink (G7, 2026-07-27).

Closes the 2026-06-08 engine gap: passing the experiments-tree run dir (holds
config/eval/train but no events file) made the engine exit 'No metrics found'.

Run: /isaac-sim/python.sh -m pytest test_resolve_events_dir.py
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import analyze_training as at
except (ImportError, SystemExit):
    pytest.skip("engine deps unavailable under this interpreter", allow_module_level=True)


def _mk_logs_run(tmp_path):
    logs = tmp_path / "logs" / "run_a"
    logs.mkdir(parents=True)
    (logs / "events.out.tfevents.123.host.1.0").touch()
    return logs


def test_logs_dir_passes_through(tmp_path):
    logs = _mk_logs_run(tmp_path)
    assert at._resolve_events_dir(logs) == logs


def test_experiments_dir_follows_train_symlink(tmp_path):
    logs = _mk_logs_run(tmp_path)
    exp = tmp_path / "experiments" / "run_a"
    exp.mkdir(parents=True)
    (exp / "train").symlink_to(logs)
    assert at._resolve_events_dir(exp) == logs.resolve()


def test_dir_without_events_or_train_unchanged(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    assert at._resolve_events_dir(d) == d
