import argparse
import sys
import os
import fcntl
import json
import time
import signal
import subprocess
import math
import itertools
from datetime import datetime

KP_VALS = [24, 34, 48, 68, 96]
KD_VALS = [7, 10, 14, 20, 28]
M_SCALES = [0.67, 1.0, 1.5]
NOMINAL_M_HAT = [0.15, 0.16]

LEAK_VALS = [0.1, 0.5, 2.0]
AG_VALS = [0.01, 0.02, 0.04]

TASKS = {
    "tdc": "Isaac-ConstrainedALBC-Main-TDC-SimToReal-v0",
    "pid": "Isaac-ConstrainedALBC-Main-PID-SimToReal-v0",
    "atdc": "Isaac-ConstrainedALBC-Main-ATDC-SimToReal-v0"
}

def check_uncommitted(code_dir):
    try:
        out = subprocess.check_output(["git", "status", "--short", "--", "constrained_albc"], cwd=code_dir, text=True, stderr=subprocess.DEVNULL)
        return len([line for line in out.splitlines() if line.strip()])
    except Exception:
        return 0

def refuse_invalid_outroot(out_root):
    abs_out = os.path.abspath(out_root)
    forbidden = [
        "/workspace/constrained-albc-eval",
        "/workspace/constrained-albc-r3a",
        "/workspace/marinelab-r3a"
    ]
    for d in forbidden:
        if abs_out == d or abs_out.startswith(d + "/"):
            print(f"FATAL: output root {out_root} is inside forbidden directory {d}", file=sys.stderr)
            sys.exit(1)

def get_grid(controller, out_root):
    if controller in ["tdc", "pid"]:
        points = []
        for kp, kd, m_scale in itertools.product(KP_VALS, KD_VALS, M_SCALES):
            name = f"kp{kp}_kd{kd}_m{m_scale:g}"
            points.append({
                "name": name,
                "kp": kp,
                "kd": kd,
                "m_hat_scale": m_scale,
                "m_hat": [NOMINAL_M_HAT[0] * m_scale, NOMINAL_M_HAT[1] * m_scale],
                "m_hat_leak": None,
                "m_hat_adapt_gain": None
            })
        return points
    else: # atdc
        tdc_sel_file = os.path.join(os.path.dirname(os.path.abspath(out_root)), "tdc", "selection.json")
        if not os.path.exists(tdc_sel_file):
            print(f"FATAL: TDC selection file missing: {tdc_sel_file}", file=sys.stderr)
            sys.exit(1)
        with open(tdc_sel_file) as f:
            tdc_sel = json.load(f)["selected"]
        
        base_kp = tdc_sel["kp"]
        base_kd = tdc_sel["kd"]
        base_m_scale = tdc_sel.get("m_hat_scale", 1.0)
        base_m_hat = tdc_sel["m_hat"]
        
        points = []
        for leak, ag in itertools.product(LEAK_VALS, AG_VALS):
            name = f"kp{base_kp}_kd{base_kd}_m{base_m_scale:g}__leak{leak:g}_ag{ag:g}"
            points.append({
                "name": name,
                "kp": base_kp,
                "kd": base_kd,
                "m_hat_scale": base_m_scale,
                "m_hat": base_m_hat,
                "m_hat_leak": leak,
                "m_hat_adapt_gain": ag
            })
        return points

def build_cmd(code_dir, p3b_dir, task, point, point_dir):
    cmd = [
        "/workspace/isaaclab/isaaclab.sh", "-p", "constrained_albc/analysis/eval.py", "static",
        "--task", task, "--checkpoint", "none", "--num_envs", "64", "--seed", "42",
        "--headless", "--fault_fixed_health", "1,1,1,1,1,1", "--att-amp-deg", "15",
        "--env-dr-anchor", "--doraemon-dr-from", p3b_dir, "--levels", "none,soft",
        "--output_dir", point_dir,
        # float() on every value: Hydra rejects an int for a float cfg field
        # (kp=24 -> "Expected float, Received int", v14 smoke V6b 2026-09-12).
        f"env.tdc_controller.kp={float(point['kp'])}",
        f"env.tdc_controller.kd={float(point['kd'])}",
        f"env.tdc_controller.m_hat=[{float(point['m_hat'][0])},{float(point['m_hat'][1])}]"
    ]
    if point["m_hat_leak"] is not None:
        cmd.append(f"env.tdc_controller.m_hat_leak={float(point['m_hat_leak'])}")
    if point["m_hat_adapt_gain"] is not None:
        cmd.append(f"env.tdc_controller.m_hat_adapt_gain={float(point['m_hat_adapt_gain'])}")
    return cmd

def get_repo_head(repo_dir):
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_dir, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller", choices=["tdc", "pid", "atdc"], required=True)
    parser.add_argument("--code", default="/workspace/constrained-albc-eval")
    parser.add_argument("--out")
    parser.add_argument("--p3b-run", default="/workspace/constrained-albc/logs/rsl_rl/albc_trpo_teacher/retrain_simtoreal_p3/trpo_p3b_lb200_s30_r2050_260904_163518")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--select", action="store_true")
    
    parser.add_argument("--allow-partial", action="store_true")
    
    args = parser.parse_args()
    
    if not args.out:
        args.out = f"/workspace/constrained-albc/.hq/work/paper_ablation_r3a/gain_search/{args.controller}/"
        
    refuse_invalid_outroot(args.out)
    
    points = get_grid(args.controller, args.out)
    
    if args.dry_run:
        for pt in points:
            pt_dir = os.path.join(args.out, pt["name"])
            cmd = build_cmd(args.code, args.p3b_run, TASKS[args.controller], pt, pt_dir)
            print(" ".join(cmd))
        return

    if args.run:
        if check_uncommitted(args.code) > 0:
            print("FATAL: uncommitted changes in code worktree", file=sys.stderr)
            sys.exit(1)
        os.makedirs(args.out, exist_ok=True)
        
        grid_data = {
            "grid": points,
            "controller": args.controller,
            "task": TASKS[args.controller],
            "p3b_dir": args.p3b_run,
            "code_HEAD": get_repo_head(args.code)
        }
        with open(os.path.join(args.out, "grid.json"), "w") as f:
            json.dump(grid_data, f, indent=2)

        marinelab_head = get_repo_head("/workspace/marinelab-r3a")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{args.code}:/workspace/marinelab-r3a"
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["TERM"] = "xterm"
        env["CUDA_VISIBLE_DEVICES"] = "1"

        lock_path = "/root/gpu1.lock"
        if not os.path.exists(lock_path):
            try:
                os.makedirs(os.path.dirname(lock_path), exist_ok=True)
                open(lock_path, "a").close()
            except Exception:
                pass
        
        for pt in points:
            if check_uncommitted(args.code) > 0:
                print(f"FATAL: uncommitted changes in code worktree before point {pt['name']}", file=sys.stderr)
                sys.exit(1)
            pt_dir = os.path.join(args.out, pt["name"])
            os.makedirs(pt_dir, exist_ok=True)
            if os.path.exists(os.path.join(pt_dir, "summary.json")):
                continue
            
            cmd = build_cmd(args.code, args.p3b_run, TASKS[args.controller], pt, pt_dir)
            
            try:
                fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)
                fcntl.flock(fd, fcntl.LOCK_EX)
            except Exception as e:
                print(f"Failed to acquire lock: {e}", file=sys.stderr)
                sys.exit(1)
            lock_acq = datetime.now().isoformat()
            if os.path.exists(os.path.join(pt_dir, "summary.json")):  # finished by another invocation while waiting
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                continue

            t0 = time.time()
            log_path = pt_dir + ".log"
            # A hung evaluator would hold the shared GPU1 lock forever: bound each point and kill its whole group.
            # ponytail: fixed 3600 s cap; a 2-tier point takes about 5 min on the 4060.
            with open(log_path, "w") as log_f:
                proc = subprocess.Popen(cmd, env=env, stdout=log_f, stderr=subprocess.STDOUT, cwd=args.code,
                                        start_new_session=True)
                try:
                    rc = proc.wait(timeout=3600)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGTERM)
                    try:
                        proc.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
                    rc = 124
                except BaseException:
                    os.killpg(proc.pid, signal.SIGTERM)
                    raise
            dur = time.time() - t0
            
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            
            uncomm_lines = check_uncommitted(args.code)
            run_cond = (
                f"command: {' '.join(cmd)}\n"
                f"code_HEAD: {grid_data['code_HEAD']}\n"
                f"marinelab_HEAD: {marinelab_head}\n"
                f"uncommitted_lines: {uncomm_lines}\n"
                f"lock_acquired: {lock_acq}\n"
                f"rc: {rc}\n"
                f"seconds: {dur:.2f}\n"
            )
            with open(os.path.join(pt_dir, "RUN_CONDITIONS.txt"), "w") as f:
                f.write(run_cond)
                
        return

    if args.select:
        rows = []
        n_completed = 0
        default_pt_name = None
        if args.controller in ["tdc", "pid"]:
            default_match = lambda p: p["kp"] == 48 and p["kd"] == 14 and p["m_hat_scale"] == 1.0
        else:
            default_match = lambda p: p["m_hat_leak"] == 0.5 and p["m_hat_adapt_gain"] == 0.02
        
        default_pt_survival = None
        
        summary_data = {}
        for pt in points:
            sum_path = os.path.join(args.out, pt["name"], "summary.json")
            if os.path.exists(sum_path):
                n_completed += 1
                with open(sum_path) as f:
                    s = json.load(f)
                summary_data[pt["name"]] = s
                if default_match(pt):
                    default_pt_name = pt["name"]
                    default_pt_survival = s.get("soft", {}).get("survival_pct", 0)
        
        if n_completed < len(points) and not args.allow_partial:
            print("FATAL: not all points completed and --allow-partial not passed", file=sys.stderr)
            sys.exit(1)
            
        if default_pt_name is None or default_pt_name not in summary_data:
            print("FATAL: default point missing or not completed", file=sys.stderr)
            sys.exit(1)
            
        valid_pts = []
        best_score = float('inf')
        
        for pt in points:
            name = pt["name"]
            if name not in summary_data:
                continue
            s = summary_data[name]
            surv = s.get("soft", {}).get("survival_pct", 0)
            score_none = s.get("none", {}).get("att_norm", {}).get("ss_error", float('inf'))
            score_soft = s.get("soft", {}).get("att_norm", {}).get("ss_error", float('inf'))
            score = (score_none + score_soft) / 2.0
            
            row = {
                "point": name,
                "kp": pt["kp"],
                "kd": pt["kd"],
                "m_hat_scale": pt["m_hat_scale"],
                "m_hat": pt["m_hat"],
                "m_hat_leak": pt["m_hat_leak"],
                "m_hat_adapt_gain": pt["m_hat_adapt_gain"],
                "score_deg": score,
                "survival_pct": surv,
                "none_ss_error": score_none,
                "soft_ss_error": score_soft
            }
            rows.append(row)
            
            if surv < default_pt_survival - 1.5625:
                continue
                
            valid_pts.append((pt, score))
            if score < best_score:
                best_score = score

        if not valid_pts:
            print("FATAL: no points available for selection after exclusion", file=sys.stderr)
            sys.exit(1)

        tied_pts = [p for p, sc in valid_pts if sc <= best_score + 0.10 + 1e-9]
        
        final_best = None
        if len(tied_pts) == 1:
            final_best = tied_pts[0]
        else:
            def log_dist(p):
                if args.controller in ["tdc", "pid"]:
                    return (abs(math.log(p["kp"] / 48.0)) +
                            abs(math.log(p["kd"] / 14.0)) +
                            abs(math.log(p["m_hat_scale"] / 1.0)))
                else:
                    return (abs(math.log(p["m_hat_leak"] / 0.5)) +
                            abs(math.log(p["m_hat_adapt_gain"] / 0.02)))
            
            min_dist = float('inf')
            dist_tied = []
            for tpt in tied_pts:
                d = log_dist(tpt)
                if d < min_dist - 1e-9:
                    min_dist = d
                    dist_tied = [tpt]
                elif abs(d - min_dist) < 1e-9:
                    dist_tied.append(tpt)
            
            if len(dist_tied) == 1:
                final_best = dist_tied[0]
            else:
                dist_tied.sort(key=lambda x: x["name"])
                final_best = dist_tied[0]
                
        out_json = {
            "controller": args.controller,
            "task": TASKS[args.controller],
            "rule": "pre-registered",
            "selected": {
                "point": final_best["name"],
                "kp": final_best["kp"],
                "kd": final_best["kd"],
                "m_hat_scale": final_best["m_hat_scale"],
                "m_hat": final_best["m_hat"],
                "m_hat_leak": final_best["m_hat_leak"],
                "m_hat_adapt_gain": final_best["m_hat_adapt_gain"],
                "score_deg": best_score
            },
            "rows": rows,
            "n_completed": n_completed,
            "n_grid": len(points)
        }
        with open(os.path.join(args.out, "selection.json"), "w") as f:
            json.dump(out_json, f, indent=2)

if __name__ == "__main__":
    main()
