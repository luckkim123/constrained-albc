import os
import sys
import subprocess
import json
import tempfile
import shutil
import re

TOOL_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "classical_gain_search.py")
PYTHON_EXE = "/opt/homebrew/bin/python3.12" if os.path.exists("/opt/homebrew/bin/python3.12") else sys.executable

def run_cmd(cmd, env=None, check=True):
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if check and res.returncode != 0:
        print(f"Command failed with rc {res.returncode}")
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        res.check_returncode()
    return res

def test_dry_run_and_grid_size():
    # dry run tdc
    res = run_cmd([PYTHON_EXE, TOOL_PATH, "--controller", "tdc", "--dry-run"])
    out = res.stdout
    assert "kp24" in out
    assert "kd7" in out
    # 75 points -> 75 lines of printed commands
    lines = [l for l in out.splitlines() if "isaaclab.sh" in l]
    assert len(lines) == 75, f"Expected 75 lines, got {len(lines)}"
    assert "--output_dir" in out
    assert "env.tdc_controller.m_hat=[" in out
    # Hydra rejects an int for a float cfg field (v14 smoke V6b: kp=24 -> ValueError)
    assert "env.tdc_controller.kp=24.0" in out and "env.tdc_controller.kd=7.0" in out
    assert not re.search(r"env\.tdc_controller\.(kp|kd)=\d+(\s|$)", out), "int-typed gain override"
    
    # ensure no point directory was created in default out
    default_out = "/workspace/constrained-albc/.hq/work/paper_ablation_r3a/gain_search/tdc/"
    if os.path.exists(default_out) and os.listdir(default_out):
        for child in os.listdir(default_out):
            assert "kp" not in child, f"Dry run should not create point directories, found {child}"

    # check ATDC dry run
    with tempfile.TemporaryDirectory() as td:
        tdc_dir = os.path.join(td, "tdc")
        os.makedirs(tdc_dir)
        with open(os.path.join(tdc_dir, "selection.json"), "w") as f:
            json.dump({
                "selected": {
                    "point": "kp48_kd14_m1",
                    "kp": 48,
                    "kd": 14,
                    "m_hat_scale": 1.0,
                    "m_hat": [0.15, 0.16]
                }
            }, f)
        
        atdc_dir = os.path.join(td, "atdc")
        res = run_cmd([PYTHON_EXE, TOOL_PATH, "--controller", "atdc", "--dry-run", "--out", atdc_dir])
        lines = [l for l in res.stdout.splitlines() if "isaaclab.sh" in l]
        assert len(lines) == 9, f"Expected 9 ATDC points, got {len(lines)}"
        assert "env.tdc_controller.m_hat_leak=" in res.stdout
        assert "env.tdc_controller.m_hat_adapt_gain=" in res.stdout
        assert "env.tdc_controller.kp=48.0" in res.stdout, "int kp from selection.json must be cast"
    print("test_dry_run_and_grid_size passed")

def test_refusals():
    for bad_dir in [
        "/workspace/constrained-albc-eval",
        "/workspace/constrained-albc-r3a",
        "/workspace/marinelab-r3a",
        "/workspace/constrained-albc-eval/some/child"
    ]:
        res = run_cmd([PYTHON_EXE, TOOL_PATH, "--controller", "tdc", "--dry-run", "--out", bad_dir], check=False)
        assert res.returncode == 1, f"Expected refusal for {bad_dir}"
        assert "FATAL" in res.stdout or "FATAL" in res.stderr
    print("test_refusals passed")

def test_selection():
    with tempfile.TemporaryDirectory() as td:
        out_dir = os.path.join(td, "tdc")
        os.makedirs(out_dir)
        
        # Test partial refusal
        res = run_cmd([PYTHON_EXE, TOOL_PATH, "--controller", "tdc", "--select", "--out", out_dir], check=False)
        assert res.returncode == 1, "Expected partial failure"
        assert "partial" in res.stdout or "partial" in res.stderr

        # Test missing default -> SystemExit
        res = run_cmd([PYTHON_EXE, TOOL_PATH, "--controller", "tdc", "--select", "--allow-partial", "--out", out_dir], check=False)
        assert res.returncode == 1, "Expected default missing failure"
        assert "default point missing" in res.stdout or "default point missing" in res.stderr

        # Create default point
        def_pt_dir = os.path.join(out_dir, "kp48_kd14_m1")
        os.makedirs(def_pt_dir)
        with open(os.path.join(def_pt_dir, "summary.json"), "w") as f:
            json.dump({
                "none": {"att_norm": {"ss_error": 1.0}},
                "soft": {"att_norm": {"ss_error": 1.0}, "survival_pct": 100.0}
            }, f)

        # Create a point that gets excluded due to survival
        bad_surv_dir = os.path.join(out_dir, "kp96_kd28_m1.5")
        os.makedirs(bad_surv_dir)
        with open(os.path.join(bad_surv_dir, "summary.json"), "w") as f:
            json.dump({
                "none": {"att_norm": {"ss_error": 0.1}}, 
                "soft": {"att_norm": {"ss_error": 0.1}, "survival_pct": 98.0} # excluded
            }, f)
        
        # Create a tied point that is far from default
        tie_far_dir = os.path.join(out_dir, "kp96_kd28_m1")
        os.makedirs(tie_far_dir)
        with open(os.path.join(tie_far_dir, "summary.json"), "w") as f:
            json.dump({
                "none": {"att_norm": {"ss_error": 0.5}},
                "soft": {"att_norm": {"ss_error": 0.5}, "survival_pct": 100.0}
            }, f)
            
        # Create a tied point that is close to default
        tie_close_dir = os.path.join(out_dir, "kp68_kd14_m1")
        os.makedirs(tie_close_dir)
        with open(os.path.join(tie_close_dir, "summary.json"), "w") as f:
            json.dump({
                "none": {"att_norm": {"ss_error": 0.55}}, # within 0.1 of 0.5
                "soft": {"att_norm": {"ss_error": 0.55}, "survival_pct": 100.0}
            }, f)
            
        # Run selection
        res = run_cmd([PYTHON_EXE, TOOL_PATH, "--controller", "tdc", "--select", "--allow-partial", "--out", out_dir])
        assert res.returncode == 0
        
        with open(os.path.join(out_dir, "selection.json")) as f:
            sel = json.load(f)
            assert sel["selected"]["point"] == "kp68_kd14_m1"
            assert sel["rule"] == "pre-registered"
    print("test_selection passed")

if __name__ == "__main__":
    test_dry_run_and_grid_size()
    test_refusals()
    test_selection()
    print("All tests passed.")
