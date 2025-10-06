import os
from datetime import datetime
import pandas as pd
import heapq
from read_file import read_jobs

# ---------------------------
# Test instance optimal profits (optional, for printout)
# ---------------------------
optimal_profits = {
    "test1": 133,
    "test2": 44,
    "test3": 30,
    "test4": 10,
    "test5": 0,
    "test6": 130,
    "test7": 70
}

# ---------------------------
# Online scheduler state
# ---------------------------
calendar = {}           # t -> job_id (or 0 if idle)
scheduled_jobs = []     # list of job dicts with annotations
total_profit = 0

# ---------------------------
# Helpers
# ---------------------------
def mark_infeasible(job):
    job["feasible"] = (job["d"] - job["r"] + 1) >= job["p"]
    return job

def compute_score(job):
    # density-like priority; used for selection
    job["score"] = (job["w"] + job["l"]) / job["p"] if job["feasible"] else -1
    return job

def annotate_job(job):
    # fields used by the simulator
    job["assigned_slots"] = []
    job["remaining"] = job["p"] if job["feasible"] else 0
    job["rejected"] = False          # infeasible-at-arrival rejection
    job["penalized_now"] = False     # to avoid double-penalizing
    return job

def log_results_csv(test_case_name, csv_file="results_log.csv"):
    global scheduled_jobs, total_profit
    rows = []
    job_details = []
    for job in scheduled_jobs:
        slots = ",".join(map(str, job["assigned_slots"])) if job["assigned_slots"] else "null"
        job_details.append(f"id:{job['id']} r:{job['r']} d:{job['d']} p:{job['p']} w:{job['w']} l:{job['l']} slots:{slots}")
    rows.append({
        "date": datetime.now().date(),
        "time": datetime.now().time().strftime("%H:%M:%S"),
        "test_case": test_case_name,
        "total_profit": total_profit,
        "job_details": " | ".join(job_details)
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
# Main online algorithm
# ---------------------------
def run_online_algorithm_from_file(input_file):
    """
    Online preemptive policy:
      - Time ticks t from min(r) to max(d).
      - At each t, consider jobs with r <= t <= d and remaining > 0.
      - Pick job with highest score = (w + l) / p. (Break ties by: higher w, earlier d, smaller id.)
      - Assign 1 unit at time t to that job (preemption allowed).
      - At the end: +w if remaining == 0; otherwise -l. Infeasible at arrival => immediate -l.
    """
    global calendar, scheduled_jobs, total_profit
    calendar = {}
    scheduled_jobs = []
    total_profit = 0

    # Load jobs
    jobs = read_jobs(input_file)

    # Preprocess jobs
    for job in jobs:
        mark_infeasible(job)
        compute_score(job)
        annotate_job(job)

    # Immediately reject infeasible jobs with penalty
    for job in jobs:
        if not job["feasible"]:
            job["rejected"] = True
            job["penalized_now"] = True
            total_profit -= job["l"]
            print(f"Job {job['id']} infeasible → -{job['l']}, slots = null")

    # If all feasible jobs are rejected, we still want to output their null lines later
    scheduled_jobs = jobs[:]  # keep original order for final output

    # Determine simulation horizon
    feasible_jobs = [j for j in jobs if j["feasible"] and not j["rejected"]]
    if feasible_jobs:
        T_min = min(j["r"] for j in feasible_jobs)
        T_max = max(j["d"] for j in feasible_jobs)
    else:
        # nothing schedulable; just finalize and save
        finalize_and_save(input_file)
        return

    # Active heap: max-heap by score (use negatives for heapq). Tie-breakers: -w, d, id
    # Entry = (-score, -w, d, id, job_ref)
    active = []
    # Jobs keyed by release times for efficient insertion
    releases = {}
    for j in feasible_jobs:
        releases.setdefault(j["r"], []).append(j)

    # Simulation over time
    for t in range(T_min, T_max + 1):
        # Add newly released jobs
        for j in releases.get(t, []):
            if j["remaining"] > 0:
                heapq.heappush(active, (-j["score"], -j["w"], j["d"], j["id"], j))

        # Drop expired or finished jobs from the top as needed
        while active and (active[0][4]["remaining"] == 0 or t > active[0][4]["d"]):
            heapq.heappop(active)

        # Also lazily skip expired/finished entries when popped later

        # Pick best available job (if any)
        chosen_job = None
        while active:
            _, _, _, _, cand = heapq.heappop(active)
            if cand["remaining"] > 0 and t <= cand["d"]:
                chosen_job = cand
                break
            # else skip finished/expired stales and keep popping

        if chosen_job is not None:
            # Assign one unit at time t
            chosen_job["assigned_slots"].append(t)
            chosen_job["remaining"] -= 1
            calendar[t] = chosen_job["id"]
            # If still has remaining and deadline not yet passed, push back for future consideration
            if chosen_job["remaining"] > 0 and t < chosen_job["d"]:
                heapq.heappush(active, (-chosen_job["score"], -chosen_job["w"], chosen_job["d"], chosen_job["id"], chosen_job))
        else:
            # Idle
            calendar[t] = 0

    # Settle rewards/penalties
    for job in jobs:
        if job["rejected"]:
            # already penalized
            continue
        if not job["feasible"]:
            # already handled as rejected
            continue
        if job["remaining"] == 0:
            total_profit += job["w"]
            print(f"Job {job['id']} DONE → +{job['w']}, slots = {job['assigned_slots']}")
        else:
            total_profit -= job["l"]
            print(f"Job {job['id']} NOT done → -{job['l']}, slots = {job['assigned_slots'] if job['assigned_slots'] else 'null'}")

    finalize_and_save(input_file)

def finalize_and_save(input_file):
    # Pretty print + persist
    base = os.path.splitext(os.path.basename(input_file))[0]
    test_case_name = f"{base}_online_highscore"
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
        print(f"Running online scheduling for {os.path.splitext(os.path.basename(input_file))[0]} (highest-score policy)\n")
        run_online_algorithm_from_file(f"test/{input_file}")
        print("\n" + "-"*50 + "\n")
