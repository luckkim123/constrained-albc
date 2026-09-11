#!/usr/bin/env python3
import argparse
import json
import math
import sys
import numpy as np
from pathlib import Path

def sanitize_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, np.generic):
        return sanitize_json(obj.item())
    return obj

def format_sig3(x):
    if x is None:
        return "—"
    if x == 0:
        return "0"
    return f"{float(x):.3g}"

def p90(x):
    return float(np.percentile(x, 90))

def calc_stats(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"mean": None, "median": None, "p90": None, "max": None, "n": 0}
    return {
        "mean": float(np.mean(x)),
        "median": float(np.median(x)),
        "p90": p90(x),
        "max": float(np.max(x)),
        "n": int(len(x))
    }

def process_level(eval_dir, level, meta):
    data_path = eval_dir / f"data_{level}.npz"
    extras_path = eval_dir / f"extras_{level}.npz"
    
    if not data_path.exists() or not extras_path.exists():
        return None
    
    data = np.load(data_path)
    extras = np.load(extras_path)
    
    time_arr = data["time"]
    actual_roll = data["actual_roll_deg"]
    actual_pitch = data["actual_pitch_deg"]
    terminated = data["terminated"]
    
    payload_mass = extras["payload_mass"]
    payload_cog_offset = extras["payload_cog_offset"]
    
    T, N = actual_roll.shape
    dt = float(np.median(np.diff(time_arr)))
    PRE = int(round(5.0 / dt))
    POST = int(round(10.0 / dt))
    HOLD = int(round(3.0 / dt))
    TAIL = int(round(5.0 / dt))
    
    k_exp = None
    if "payload_toggle" in meta and "steps" in meta["payload_toggle"]:
        k_exp = meta["payload_toggle"]["steps"] - 1
        
    per_env = []
    counts = {"ok": 0, "terminated_before_toggle": 0, "no_toggle": 0, "multiple_changes": 0, "window_short": 0, "n_env": N}
    
    for env in range(N):
        term_idx = np.where(terminated[:, env])[0]
        if len(term_idx) > 0:
            alive_until = int(term_idx[0])
        else:
            alive_until = T
            
        survived = (alive_until == T)
        
        mass = payload_mass[:, env]
        mass_diff = np.abs(mass[1:alive_until] - mass[0:alive_until-1])
        change_indices = np.where(mass_diff > 1e-6)[0] + 1
        
        if len(change_indices) == 1:
            k = int(change_indices[0])
            if k < PRE or k + POST > T:
                status = "window_short"
            else:
                status = "ok"
        elif len(change_indices) == 0:
            if k_exp is None or alive_until <= k_exp + 2:
                status = "terminated_before_toggle"
            else:
                status = "no_toggle"
        else:
            status = "multiple_changes"
            
        counts[status] += 1
        
        env_result = {
            "env": env,
            "status": status,
            "direction": None,
            "k": None,
            "toggle_s": None,
            "alive_until": alive_until,
            "survived": survived,
            "mass_before": None,
            "mass_after": None,
            "cog_norm_m": None,
            "roll": None,
            "pitch": None
        }
        
        if status == "ok":
            k = int(change_indices[0])
            env_result["k"] = k
            env_result["toggle_s"] = float(time_arr[k])
            
            mass_before = float(mass[k-1])
            mass_after = float(mass[k])
            env_result["mass_before"] = mass_before
            env_result["mass_after"] = mass_after
            
            if mass_before <= 1e-6 < mass_after:
                direction = "pick"
                cog_norm_m = float(np.linalg.norm(payload_cog_offset[k, env]))
            elif mass_before > 1e-6 >= mass_after:
                direction = "drop"
                cog_norm_m = float(np.linalg.norm(payload_cog_offset[k-1, env]))
            else:
                direction = "change"
                cog_norm_m = float(np.linalg.norm(payload_cog_offset[k-1, env]))
                
            env_result["direction"] = direction
            env_result["cog_norm_m"] = cog_norm_m
            
            for axis_name, theta_all in [("roll", actual_roll), ("pitch", actual_pitch)]:
                theta = theta_all[:, env]
                
                W_pre_start = k - PRE
                W_pre_end = k
                W_post_start = k
                W_post_end = min(k + POST, alive_until)
                
                pre_mean = float(np.mean(theta[W_pre_start:W_pre_end]))
                pre_ss_err_deg = float(np.mean(np.abs(theta[W_pre_start:W_pre_end])))
                
                post_theta = theta[W_post_start:W_post_end]
                if len(post_theta) == 0:
                    peak_deviation_deg = 0.0
                else:
                    peak_deviation_deg = float(np.max(np.abs(post_theta))) - pre_ss_err_deg
                    
                dev = np.abs(theta - pre_mean)
                band = max(0.5, 0.10 * max(peak_deviation_deg, 0.0))
                
                if len(post_theta) == 0:
                    settling_time_s = 0.0
                else:
                    dev_W_post = dev[W_post_start:W_post_end]
                    if np.max(dev_W_post) <= band:
                        settling_time_s = 0.0
                    else:
                        p = W_post_start + int(np.argmax(dev_W_post))
                        settling_time_s = None
                        for i in range(p, alive_until - HOLD + 1):
                            if np.all(dev[i:i+HOLD] <= band):
                                settling_time_s = float(time_arr[i] - time_arr[k])
                                break
                                
                if survived:
                    post_ss_err_deg = float(np.mean(np.abs(theta[T-TAIL:T])))
                else:
                    post_ss_err_deg = None
                    
                env_result[axis_name] = {
                    "pre_ss_err_deg": pre_ss_err_deg,
                    "peak_deviation_deg": peak_deviation_deg,
                    "settling_time_s": settling_time_s,
                    "post_ss_err_deg": post_ss_err_deg
                }
                
        per_env.append(env_result)
        
    instrument_ok = (counts["no_toggle"] + counts["multiple_changes"] + counts["window_short"] == 0)
    survival_fraction_val = float(np.mean([e["survived"] for e in per_env]))
    survival_fraction = {"mean": survival_fraction_val, "n": N}
    
    step_agg = {}
    metrics_agg = {}
    
    for d in ["pick", "drop", "change"]:
        d_envs = [e for e in per_env if e["status"] == "ok" and e["direction"] == d]
        if not d_envs:
            continue
            
        step_agg[d] = {
            "mass_before": calc_stats([e["mass_before"] for e in d_envs]),
            "mass_after": calc_stats([e["mass_after"] for e in d_envs]),
            "cog_norm_m": calc_stats([e["cog_norm_m"] for e in d_envs])
        }
        
        metrics_agg[d] = {}
        for axis in ["roll", "pitch"]:
            metrics_agg[d][axis] = {}
            for metric in ["peak_deviation_deg", "settling_time_s", "pre_ss_err_deg", "post_ss_err_deg"]:
                vals = [e[axis][metric] for e in d_envs if e[axis][metric] is not None]
                stats = calc_stats(vals)
                if metric == "settling_time_s":
                    stats["n_unsettled"] = len([e for e in d_envs if e[axis][metric] is None])
                metrics_agg[d][axis][metric] = stats
                
    return {
        "counts": counts,
        "instrument_ok": instrument_ok,
        "survival_fraction": survival_fraction,
        "step": step_agg,
        "metrics": metrics_agg,
        "per_env": per_env
    }

def generate_md(results):
    md = ["| level | direction | axis | peak dev [deg] mean / median / P90 / max | settling [s] mean / median / P90 / max (unsettled) | pre-ss [deg] mean | post-ss [deg] mean | survival | n |", 
          "|---|---|---|---|---|---|---|---|---|"]
    
    counts_lines = []
    
    for level, ldata in results["levels"].items():
        surv_str = format_sig3(ldata["survival_fraction"]["mean"])
        counts = ldata["counts"]
        counts_str = ", ".join(f"{k}: {v}" for k, v in counts.items())
        counts_lines.append(f"**{level} counts**: {counts_str}")
        
        if not ldata.get("metrics"):
            continue
            
        for direction, ddata in ldata["metrics"].items():
            for axis, adata in ddata.items():
                peak = adata["peak_deviation_deg"]
                peak_str = f'{format_sig3(peak["mean"])} / {format_sig3(peak["median"])} / {format_sig3(peak["p90"])} / {format_sig3(peak["max"])}'
                
                settle = adata["settling_time_s"]
                unsettled_str = f' ({settle.get("n_unsettled", 0)})'
                settle_str = f'{format_sig3(settle["mean"])} / {format_sig3(settle["median"])} / {format_sig3(settle["p90"])} / {format_sig3(settle["max"])}{unsettled_str}'
                
                pre_ss_str = format_sig3(adata["pre_ss_err_deg"]["mean"])
                post_ss_str = format_sig3(adata["post_ss_err_deg"]["mean"])
                
                n = peak["n"]
                md.append(f"| {level} | {direction} | {axis} | {peak_str} | {settle_str} | {pre_ss_str} | {post_ss_str} | {surv_str} | {n} |")
                
    return "\n".join(md) + "\n\n" + "\n".join(counts_lines) + "\n"

def selftest():
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
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
            
        res = process_level(d, "test", meta)
        
        envs = {e["env"]: e for e in res["per_env"]}
        assert envs[0]["status"] == "ok"
        assert envs[0]["direction"] == "pick"
        assert abs(envs[0]["roll"]["peak_deviation_deg"] - 4.0) < 1e-6
        assert envs[0]["roll"]["settling_time_s"] > 0
        
        assert envs[1]["status"] == "ok"
        assert envs[1]["direction"] == "drop"
        assert envs[1]["mass_before"] > 0
        assert envs[1]["mass_after"] == 0
        
        assert envs[2]["status"] == "terminated_before_toggle"
        assert envs[3]["status"] == "no_toggle"
        
        assert envs[4]["status"] == "ok"
        assert not envs[4]["survived"]
        assert envs[4]["roll"]["post_ss_err_deg"] is None
        
        assert 7.0 <= envs[5]["roll"]["settling_time_s"] <= 10.0
        assert envs[6]["roll"]["settling_time_s"] is None
        assert res["metrics"]["pick"]["roll"]["settling_time_s"]["n_unsettled"] >= 1
        
        vals = [e["roll"]["peak_deviation_deg"] for e in res["per_env"] if e["status"] == "ok" and e["direction"] == "pick"]
        assert abs(res["metrics"]["pick"]["roll"]["peak_deviation_deg"]["p90"] - np.percentile(vals, 90)) < 1e-6
        
        def raise_on_constant(c): raise ValueError(f"Invalid constant: {c}")
        json.loads(json.dumps(sanitize_json(res)), parse_constant=raise_on_constant)
        print("selftest ok")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("eval_dir", nargs="?")
    parser.add_argument("--levels", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--md", default="")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        selftest()
        sys.exit(0)

    if not args.eval_dir:
        parser.error("eval_dir is required unless --selftest")
        
    eval_dir = Path(args.eval_dir)
    
    if args.levels:
        levels_to_process = args.levels.split(",")
    else:
        candidates = ["none", "soft", "medium", "hard", "ood"]
        levels_to_process = []
        for c in candidates:
            if (eval_dir / f"data_{c}.npz").exists() and (eval_dir / f"extras_{c}.npz").exists():
                levels_to_process.append(c)
                
    if not levels_to_process:
        print("No levels found.")
        sys.exit(1)

    meta_path = eval_dir / "extras_meta.json"
    meta = {}
    if meta_path.exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)
            
    results = {
        "eval_dir": str(eval_dir.resolve()),
        "meta": meta,
        "definitions": {
            "peak_deviation_deg": "max |theta| in the 10 s after the toggle minus the mean |theta| of the 5 s before",
            "settling_time_s": "first time after peak where dev stays <= max(0.5, 0.10 * max(peak_deviation_deg, 0)) for 3s",
            "pre_ss_err_deg": "mean(|theta|) over 5s before toggle",
            "post_ss_err_deg": "mean(|theta|) over last 5s of episode"
        },
        "levels": {}
    }
    
    missing_inputs = False
    all_ok = True
    
    for level in levels_to_process:
        res = process_level(eval_dir, level, meta)
        if res is None:
            print(f"{level}: missing inputs")
            missing_inputs = True
            continue
            
        results["levels"][level] = res
        if not res["instrument_ok"]:
            all_ok = False
            
        counts_str = ", ".join(f"{k}: {v}" for k, v in res["counts"].items())
        print(f"{level}: {counts_str}")
        
    out_json = eval_dir / "grasp_step_readout.json"
    if args.out:
        out_json = Path(args.out)
    with open(out_json, "w") as f:
        json.dump(sanitize_json(results), f, indent=2)
        
    out_md = eval_dir / "grasp_step_readout.md"
    if args.md:
        out_md = Path(args.md)
    with open(out_md, "w") as f:
        f.write(generate_md(results))
        
    if missing_inputs:
        sys.exit(1)
    if not all_ok:
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
