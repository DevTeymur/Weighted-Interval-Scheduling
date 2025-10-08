import os
from datetime import datetime
import pandas as pd
from itertools import combinations
from read_file import read_jobs

# Test instance optimal profits for reference
optimal_profits = {
    "test1": 133,
    "test2": 44,
    "test3": 15,
    "test4": 10,
    "test5": 0,
    "test6": 130,
    "test7": 70
}

def get_time_horizon(jobs):
    return max(job["d"] for job in jobs)

def dp_schedule(jobs, test_case_name):
    n = len(jobs)
    jobs = sorted(jobs, key=lambda x: x["d"])
    
    # Check time horizon limit for bitmask approach
    max_time = get_time_horizon(jobs)
    if max_time > 62:  # Safe limit for 64-bit systems
        print(f"Error: Time horizon ({max_time}) exceeds bitmask limit (62). Need alternative approach.")
        return {}, 0

    from functools import lru_cache
    @lru_cache(None)
    def dp(i, used_mask):
        if i == n:
            return 0
        job = jobs[i]
        best = -10**9
        skip_profit = -job["l"] + dp(i+1, used_mask)
        best = max(best, skip_profit)
        
        avail = [t for t in range(job["r"], job["d"] + 1) if not (used_mask >> t) & 1]
        if len(avail) >= job["p"]:
            best_take = -10**9
            for S in combinations(avail, job["p"]):
                new_mask = used_mask
                for t in S:
                    new_mask |= (1 << t)
                best_take = max(best_take, job["w"] + dp(i + 1, new_mask))
            best = max(best, best_take)
        return best

    total_profit = dp(0, 0)
    assigned = {job["id"]: [] for job in jobs}
    status = {}
    scheduled_jobs = []

    def reconstruct(i, used_mask):
        if i == n:
            return
        job = jobs[i]
        skip_profit = -job["l"] + dp(i+1, used_mask)
        best = dp(i, used_mask)
        if best == skip_profit:
            status[job["id"]] = f"NOT done → -{job['l']}"
            job["assigned_slots"] = None
            scheduled_jobs.append(job)
            reconstruct(i+1, used_mask)
            return
        
        avail = [t for t in range(job["r"], job["d"] + 1) if not (used_mask >> t) & 1]
        if best != skip_profit:
            best_S = None
            best_take = -10**9
            for S in combinations(avail, job["p"]):
                nm = used_mask
                for t in S:
                    nm |= (1 << t)
                val = job["w"] + dp(i + 1, nm)
                if val > best_take:
                    best_take, best_S = val, S
            
            # assign best_S
            new_mask = used_mask
            slots = []
            for t in best_S:
                new_mask |= (1 << t)
                assigned[job["id"]].append(t)
                slots.append(t)
            status[job["id"]] = f"DONE → +{job['w']}"
            job["assigned_slots"] = sorted(slots)
            scheduled_jobs.append(job)
            reconstruct(i+1, new_mask)

    reconstruct(0, 0)

    # Pretty print with optimal comparison
    print("Schedule results:")
    for job in jobs:
        slots = assigned[job["id"]]
        print(f"Job {job['id']} {status[job['id']]}, slots = {slots if slots else 'null'}")
    
    # Extract base test name for optimal lookup
    base_test_name = test_case_name.replace('_offline', '').replace('_online', '')
    optimal = optimal_profits.get(base_test_name, 'N/A')
    print(f"\nTotal profit: {total_profit} | Optimal: {optimal}")

    # Save results
    save_results_txt(test_case_name, scheduled_jobs, total_profit)
    log_results_csv(test_case_name, scheduled_jobs, total_profit)

    return assigned, total_profit

# ---------------------------
# Save results to CSV
# ---------------------------
def log_results_csv(test_case_name, scheduled_jobs, total_profit, csv_file="results_log.csv"):
    job_details = []
    for job in scheduled_jobs:
        slots = ",".join(map(str, job.get("assigned_slots", []))) if job.get("assigned_slots") else "null"
        job_details.append(f"id:{job['id']} r:{job['r']} d:{job['d']} p:{job['p']} w:{job['w']} l:{job['l']} slots:{slots}")
    log_data = {
        "date": datetime.now().date(),
        "time": datetime.now().time().strftime("%H:%M:%S"),
        "test_case": test_case_name,
        "total_profit": total_profit,
        "job_details": " | ".join(job_details)
    }
    df_log = pd.DataFrame([log_data])
    if os.path.exists(csv_file):
        df_log.to_csv(csv_file, mode="a", index=False, header=False)
    else:
        df_log.to_csv(csv_file, index=False, header=True)

# ---------------------------
# Save results to txt file
# ---------------------------
def save_results_txt(test_case_name, scheduled_jobs, total_profit, output_folder="results"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_path = os.path.join(output_folder, f"{test_case_name}_offline.txt")
    with open(output_path, "w") as f:
        for job in sorted(scheduled_jobs, key=lambda x: x["id"]):
            if job.get("assigned_slots"):
                f.write(",".join(map(str, job["assigned_slots"])) + "\n")
            else:
                f.write("null\n")
        f.write(str(total_profit) + "\n")
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    test_cases = ["test1", "test2", "test3", "test4", "test5", "test6", "test7"]
    for test_case in test_cases:
        jobs = read_jobs(f"test/{test_case}.txt")
        assigned, profit = dp_schedule(jobs, test_case)
        print("\n" + "-"*50 + "\n")