import os
from datetime import datetime
import pandas as pd
from read_file import read_jobs

# Optional: known optimal profits for printout
optimal_profits = {
    "test1": 133, "test2": 44, "test3": 30, "test4": 10, "test5": 0, "test6": 130, "test7": 70
}

# ---------------------------
# Config for the scoring exponents
# ---------------------------
A = 1.0  # exponent for (w + l)
B = 1.0  # exponent for p
C = 1.0  # exponent for frac_time_left
D = 1.0  # exponent for frac_work_left
EPS = 1e-12  # numerical safety

# ---------------------------
# Global state
# ---------------------------
calendar = {}           # t -> job_id (or 0 if idle)
scheduled_jobs = []     # list of annotated job dicts
total_profit = 0

# ---------------------------
# Helpers
# ---------------------------
def mark_infeasible(job):
    # Feasible if there are at least p usable slots in [r, d]
    job["feasible"] = (job["d"] - job["r"] + 1) >= job["p"]
    return job

def annotate_job(job):
    job["assigned_slots"] = []
    job["remaining"] = job["p"] if job["feasible"] else 0
    job["rejected"] = False
    return job

def frac_time_left(job, t):
    # proportion of window remaining at time t (inclusive)
    window = max(job["d"] - job["r"] + 1, 1)
    left = max(job["d"] - t + 1, 0)
    return max(left / window, EPS)

def frac_work_left(job):
    if job["p"] <= 0:
        return 1.0  # degenerate, but won't be scheduled
    return max(job["remaining"] / job["p"], EPS)

def dynamic_score(job, t):
    # (w+l)^A / (p^B * frac_time_left^C * frac_work_left^D)
    if job["remaining"] <= 0:
        return -float("inf")
    num = (job["w"] + job["l"]) ** A
    denom = (max(job["p"], EPS) ** B) * (frac_time_left(job, t) ** C) * (frac_work_left(job) ** D)
    return num / denom

def log_results_csv(test_case_name, csv_file="results_log.csv"):
    global scheduled_jobs, total_profit
    rows = []
    details = []
    for job in scheduled_jobs:
        slots = ",".join(map(str, job["assigned_slots"])) if job["assigned_slots"] else "null"
        details.append(
            f"id:{job['id']} r:{job['r']} d:{job['d']} p:{job['p']} w:{job['w']} l:{job['l']} slots:{slots}"
        )
    rows.append({
        "date": datetime.now().date(),
        "time": datetime.now().time().strftime("%H:%M:%S"),
        "test_case": test_case_name,
        "total_profit": total_profit,
        "job_details": " | ".join(details),
    })
    df = pd.DataFrame(rows)
    if os.path.exists(csv_file):
        df.to_csv(csv_file, mode="a", index=False, header=False)
    else:
        df.to_csv(csv_file, index=False, header=True)

def save_results_txt(test_case_name, output_folder="results"):
    global scheduled_jobs, total_profit
    os.makedirs(output_folder, exist_ok=True)
    path = os.path.join(output_folder, f"{test_case_name}.txt")
    with open(path, "w") as f:
        for job in sorted(scheduled_jobs, key=lambda x: x["id"]):
            if job["assigned_slots"]:
                f.write(",".join(map(str, job["assigned_slots"])) + "\n")
            else:
                f.write("null\n")
        f.write(str(total_profit) + "\n")
    print(f"\nResults saved to {path}")

# ---------------------------
# Main online algorithm (dynamic-score policy)
# ---------------------------
def run_online_algorithm_from_file(input_file):
    """
    Online preemptive scheduling with dynamic score:
      score_t = (w + l)^A / (p^B * frac_time_left(t)^C * frac_work_left(t)^D).
    At each integer time t, among jobs with r <= t <= d and remaining > 0,
    pick the job with maximum current score; break ties by higher w, earlier d, smaller id.
    """
    global calendar, scheduled_jobs, total_profit
    calendar = {}
    scheduled_jobs = []
    total_profit = 0

    jobs = read_jobs(input_file)

    # Preprocess
    for job in jobs:
        mark_infeasible(job)
        annotate_job(job)

    # Immediate penalties for infeasible on arrival
    for job in jobs:
        if not job["feasible"]:
            job["rejected"] = True
            total_profit -= job["l"]
            print(f"Job {job['id']} infeasible → -{job['l']}, slots = null")

    scheduled_jobs = jobs[:]  # keep for final writeout

    feasible = [j for j in jobs if j["feasible"] and not j["rejected"]]
    if not feasible:
        finalize_and_save(input_file)
        return

    T_min = min(j["r"] for j in feasible)
    T_max = max(j["d"] for j in feasible)

    # Group by release for O(1) arrivals
    releases = {}
    for j in feasible:
        releases.setdefault(j["r"], []).append(j)

    active = []  # simple list; we recompute scores each step for clarity

    for t in range(T_min, T_max + 1):
        # Add newly released jobs
        for j in releases.get(t, []):
            if j["remaining"] > 0:
                active.append(j)

        # Remove expired / finished from active
        active = [j for j in active if j["remaining"] > 0 and t <= j["d"]]

        # Pick job with max dynamic score (tie-breakers: w desc, d asc, id asc)
        if active:
            # Compute scores
            best = None
            best_key = None
            for j in active:
                s = dynamic_score(j, t)
                # We maximize (s, w, -d, -id) effectively
                key = (s, j["w"], -j["d"], -j["id"])
                if (best is None) or (key > best_key):
                    best = j
                    best_key = key
            # Execute one unit on the chosen job
            best["assigned_slots"].append(t)
            best["remaining"] -= 1
            calendar[t] = best["id"]
        else:
            calendar[t] = 0  # idle

    # Settle rewards/penalties
    for job in jobs:
        if job["rejected"]:
            continue
        if not job["feasible"]:
            continue
        if job["remaining"] == 0:
            total_profit += job["w"]
            print(f"Job {job['id']} DONE → +{job['w']}, slots = {job['assigned_slots']}")
        else:
            total_profit -= job["l"]
            print(f"Job {job['id']} NOT done → -{job['l']}, slots = {job['assigned_slots'] if job['assigned_slots'] else 'null'}")

    finalize_and_save(input_file)

def finalize_and_save(input_file):
    base = os.path.splitext(os.path.basename(input_file))[0]
    test_case_name = f"{base}_online_dynscore"
    base_for_opt = base.replace('_online','').replace('_offline','')
    optimal = optimal_profits.get(base_for_opt, 'N/A')
    print(f"\nFinal total profit: {total_profit} | Optimal: {optimal}")
    log_results_csv(test_case_name)
    save_results_txt(test_case_name)

# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    tests = ["test1.txt", "test2.txt", "test3.txt", "test4.txt", "test5.txt", "test6.txt", "test7.txt"]
    for input_file in tests:
        print(f"Running online scheduling for {os.path.splitext(os.path.basename(input_file))[0]} (dynamic score policy)\n")
        run_online_algorithm_from_file(f"test/{input_file}")
        print("\n" + "-"*50 + "\n")
