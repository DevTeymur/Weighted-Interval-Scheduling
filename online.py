import os
from datetime import datetime
import pandas as pd
from read_file import read_jobs

# Test instance optimal profits for reference
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
calendar = {}
scheduled_jobs = []
total_profit = 0

# ---------------------------
# Scheduler functions
# ---------------------------
def filter_infeasible(job):
    job["feasible"] = job["d"] - job["r"] + 1 >= job["p"]
    return job

def compute_score(job):
    job["score"] = (job["w"] + job["l"]) / job["p"] if job["feasible"] else -1
    return job

def schedule_job(job):
    global calendar, total_profit
    if not job["feasible"]:
        job["assigned_slots"] = None
        total_profit -= job["l"]
        print(f"Job {job['id']} NOT done → -{job['l']}, slots = null")
        scheduled_jobs.append(job)
        return job

    needed = job["p"]
    available_slots = [t for t in range(job["r"], job["d"] + 1) if calendar.get(t,0)==0]

    if len(available_slots) >= needed:
        job["assigned_slots"] = available_slots[:needed]
        for t in job["assigned_slots"]:
            calendar[t] = job["id"]
        total_profit += job["w"]
        print(f"Job {job['id']} DONE → +{job['w']}, slots = {job['assigned_slots']}")
    else:
        job["assigned_slots"] = None
        total_profit -= job["l"]
        print(f"Job {job['id']} NOT done → -{job['l']}, slots = null")

    scheduled_jobs.append(job)
    return job

# ---------------------------
# Save results to CSV
# ---------------------------
def log_results_csv(test_case_name, csv_file="results_log.csv"):
    global scheduled_jobs, total_profit
    job_details = []
    for job in scheduled_jobs:
        slots = ",".join(map(str, job["assigned_slots"])) if job["assigned_slots"] else "null"
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
def save_results_txt(test_case_name, output_folder="results"):
    global scheduled_jobs, total_profit
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_path = os.path.join(output_folder, f"{test_case_name}.txt")

    with open(output_path, "w") as f:
        for job in sorted(scheduled_jobs, key=lambda x: x["id"]):
            if job["assigned_slots"]:
                f.write(",".join(map(str, job["assigned_slots"])) + "\n")
            else:
                f.write("null\n")
        f.write(str(total_profit) + "\n")

    print(f"\nResults saved to {output_path}")



# ---------------------------
# Main online execution
# ---------------------------
def run_online_algorithm_from_file(input_file):
    global calendar, scheduled_jobs, total_profit
    # reset state
    calendar = {}
    scheduled_jobs = []
    total_profit = 0

    jobs = read_jobs(input_file)
    test_case_name = os.path.splitext(os.path.basename(input_file))[0] + "_online"
    print(f"Running online scheduling for {test_case_name}\n")

    for job in jobs:
        job = filter_infeasible(job)
        job = compute_score(job)
        schedule_job(job)
    
    # Extract base test name (without _online or .txt)
    base_test_name = os.path.splitext(os.path.basename(input_file))[0]
    optimal = optimal_profits.get(base_test_name.replace('_online','').replace('_offline',''), 'N/A')
    print(f"\nFinal total profit: {total_profit} | Optimal: {optimal}")
    log_results_csv(test_case_name)
    save_results_txt(test_case_name)

# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    tests = ["test1.txt", "test2.txt", "test3.txt", "test4.txt", "test5.txt", "test6.txt", "test7.txt"]
    for input_file in tests:
        run_online_algorithm_from_file(f'test/{input_file}')
        print("\n" + "-"*50 + "\n")
