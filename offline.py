import os
from datetime import datetime
import pandas as pd
from read_file import read_jobs

# 1. Discard infeasible jobs
def filter_infeasible(jobs):
    for job in jobs:
        if job["d"] - job["r"] + 1 < job["p"]:
            job["feasible"] = False
        else:
            job["feasible"] = True
    return jobs

# 2. Compute slack and score
def compute_scores(jobs):
    for job in jobs:
        if job["feasible"]:
            slack = job["d"] - job["r"] + 1 - job["p"]
            job["slack"] = slack
            job["score"] = round((job["w"] + job["l"]) / job["p"] * (1/(slack+1)), 3)
        else:
            job["slack"] = None
            job["score"] = -1  # infeasible jobs get lowest score
    return jobs

# 3. Sort jobs
def sort_jobs(jobs):
    # descending score, tie-break: smaller p, then earlier d
    jobs_sorted = sorted(
        jobs,
        key=lambda x: (-x["score"], x["p"], x["d"])
    )
    return jobs_sorted

# 4. Greedy latest-slot scheduling
def schedule_jobs(jobs):
    # maintain a calendar of used slots
    max_time = max(job["d"] for job in jobs)
    calendar = [0] * (max_time + 1)  # index 1..max_time
    
    for job in jobs:
        if not job["feasible"]:
            continue
        needed = job["p"]
        slots = []
        # try to assign latest available slots in [r,d]
        for t in range(job["d"], job["r"]-1, -1):
            if calendar[t] == 0:
                slots.append(t)
                if len(slots) == needed:
                    break
        if len(slots) == needed:
            job["assigned_slots"] = sorted(slots)
            for t in slots:
                calendar[t] = 1
        else:
            job["assigned_slots"] = None
            job["feasible"] = False
    return jobs

# 5. Write output text file
def write_output(jobs, test_case_name, output_folder="results"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Compute total profit
    total_profit = sum(job["w"] for job in jobs if job["assigned_slots"]) \
                   - sum(job["l"] for job in jobs if not job["assigned_slots"])
    
    # Find available filename with increment
    i = 1
    while True:
        output_path = os.path.join(output_folder, f"{test_case_name}_{i}.txt")
        if not os.path.exists(output_path):
            break
        i += 1
    
    # Write the output file
    with open(output_path, "w") as f:
        for job in sorted(jobs, key=lambda x: x["id"]):
            if job["assigned_slots"]:
                f.write(",".join(map(str, job["assigned_slots"])) + "\n")
            else:
                f.write("null\n")
        f.write(str(total_profit) + "\n")
    
    return total_profit

# 6. Log results to CSV
def log_results_csv(test_case_name, jobs, total_profit, csv_file="results_log.csv"):
    # Prepare summary log
    log_data = {
        "date": datetime.now().date(),
        "time": datetime.now().time().strftime("%H:%M:%S"),
        "test_case": test_case_name,
        "total_profit": total_profit
    }
    
    # Job-level details as a string
    job_details = []
    for job in jobs:
        slots = ",".join(map(str, job["assigned_slots"])) if job["assigned_slots"] else "null"
        job_details.append(f"id:{job['id']} r:{job['r']} d:{job['d']} p:{job['p']} w:{job['w']} l:{job['l']} slots:{slots}")
    
    log_data["job_details"] = " | ".join(job_details)
    
    df_log = pd.DataFrame([log_data])
    
    # Append if file exists, else create
    if os.path.exists(csv_file):
        df_log.to_csv(csv_file, mode="a", index=False, header=False)
    else:
        df_log.to_csv(csv_file, index=False, header=True)


# Main execution for a test case
def run_offline_algorithm(input_file, test_case_name):
    jobs = read_jobs(input_file)
    print(f"Read {len(jobs)} jobs from {input_file}")
    jobs = filter_infeasible(jobs)
    jobs = compute_scores(jobs)
    jobs = sort_jobs(jobs)
    jobs = schedule_jobs(jobs)
    total_profit = write_output(jobs, test_case_name)
    log_results_csv(test_case_name, jobs, total_profit)
    print("Jobs:", jobs)
    print()
    print(f"Test case {test_case_name} done. Total profit: {total_profit}")


# Example run
if __name__ == "__main__":
    input_file = "test/test7.txt"
    test_case_name = os.path.splitext(os.path.basename(input_file))[0]
    run_offline_algorithm(input_file, test_case_name)
