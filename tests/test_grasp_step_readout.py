import sys
import json
import numpy as np
import tempfile
import subprocess
import importlib.util
from pathlib import Path

def generate_test_data(d):
    T, N, dt = 1500, 7, 0.02
    time_arr = np.arange(T) * dt
    actual_roll_deg = np.zeros((T, N))
    actual_pitch_deg = np.zeros((T, N))
    terminated = np.zeros((T, N), dtype=bool)
    payload_mass = np.zeros((T, N), dtype=np.float32)
    payload_cog_offset = np.zeros((T, N, 3), dtype=np.float32)
    
    # Env 0 (Case 1): pick at 750
    payload_mass[750:, 0] = 1.0
    actual_roll_deg[750:775, 0] = np.linspace(0, 4, 25)
    actual_roll_deg[775:800, 0] = np.linspace(4, 0, 25)
    
    # Env 1 (Case 2): drop at 750
    payload_mass[:750, 1] = 1.0
    payload_mass[750:, 1] = 0.0
    
    # Env 2 (Case 3): terminated at 300, mass change 301
    terminated[300:, 2] = True
    payload_mass[301:, 2] = 1.0
    
    # Env 3 (Case 4): alive to end, no mass change
    
    # Env 4 (Case 5): toggle at 750, term 1200, mass change 1201
    payload_mass[750:, 4] = 1.0
    terminated[1200:, 4] = True
    payload_mass[1201:, 4] = 2.0
    
    # Env 5 (Case 6): slow transient
    payload_mass[750:, 5] = 1.0
    actual_roll_deg[750:950, 5] = 0.1
    actual_roll_deg[950:1050, 5] = np.linspace(0.1, 3, 100)
    actual_roll_deg[1050:1200, 5] = np.linspace(3, 0, 150)
    
    # Env 6 (Case 7): never settles
    payload_mass[750:, 6] = 1.0
    actual_roll_deg[750:, 6] = 2.0 * np.sin(np.arange(T - 750) * 0.1)

    np.savez(d / "data_test.npz", time=time_arr, actual_roll_deg=actual_roll_deg, 
             actual_pitch_deg=actual_pitch_deg, terminated=terminated)
    np.savez(d / "extras_test.npz", payload_mass=payload_mass, payload_cog_offset=payload_cog_offset)
    
    meta = {"payload_toggle": {"steps": 751}}
    with open(d / "extras_meta.json", "w") as f:
        json.dump(meta, f)

def load_readout_module():
    ROOT = Path(__file__).resolve().parents[1]
    tool_path = ROOT / "tools/grasp_step_readout.py"
    spec = importlib.util.spec_from_file_location("readout", tool_path)
    readout = importlib.util.module_from_spec(spec)
    sys.modules["readout"] = readout
    spec.loader.exec_module(readout)
    return readout, tool_path

def test_cases():
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        generate_test_data(d)
        readout, tool_path = load_readout_module()
        
        meta = {"payload_toggle": {"steps": 751}}
        res = readout.process_level(d, "test", meta)
        envs = {e["env"]: e for e in res["per_env"]}
        
        # Case 1
        assert envs[0]["status"] == "ok"
        assert envs[0]["direction"] == "pick"
        assert abs(envs[0]["roll"]["peak_deviation_deg"] - 4.0) < 1e-6
        assert envs[0]["roll"]["settling_time_s"] > 0
        
        # Case 2
        assert envs[1]["status"] == "ok"
        assert envs[1]["direction"] == "drop"
        assert envs[1]["mass_before"] > 0
        assert envs[1]["mass_after"] == 0
        
        # Case 3
        assert envs[2]["status"] == "terminated_before_toggle"
        
        # Case 4
        assert envs[3]["status"] == "no_toggle"
        
        # Case 5
        assert envs[4]["status"] == "ok"
        assert not envs[4]["survived"]
        assert envs[4]["roll"]["post_ss_err_deg"] is None
        
        # Case 6
        settle_6 = envs[5]["roll"]["settling_time_s"]
        assert 7.0 <= settle_6 <= 10.0
        
        # Case 7
        assert envs[6]["roll"]["settling_time_s"] is None
        assert res["metrics"]["pick"]["roll"]["settling_time_s"]["n_unsettled"] >= 1
        
        # Case 8
        vals = [e["roll"]["peak_deviation_deg"] for e in res["per_env"] if e["status"] == "ok" and e["direction"] == "pick"]
        p90_val = res["metrics"]["pick"]["roll"]["peak_deviation_deg"]["p90"]
        assert abs(p90_val - np.percentile(vals, 90)) < 1e-6
        
        j_str = json.dumps(readout.sanitize_json(res))
        def raise_on_constant(c): raise ValueError(f"Invalid constant: {c}")
        json.loads(j_str, parse_constant=raise_on_constant)
        
        # CLI exit code test
        cmd = [sys.executable, str(tool_path), str(d), "--levels", "test"]
        proc = subprocess.run(cmd, capture_output=True)
        assert proc.returncode == 2

if __name__ == "__main__":
    test_cases()
    print("All tests passed.")
