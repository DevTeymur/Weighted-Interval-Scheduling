import os
from read_file import read_jobs

def get_time_horizon(jobs):
    return max(job["d"] for job in jobs)
    # return max(job["d"]-1 for job in jobs)   # since deadline is exclusive


def dp_schedule(jobs):
    """
    DP for optimal offline schedule (preemptive).
    Idea: jobs sorted by deadline. State is index of job and available time slots.
    For simplicity: brute-force DP over subsets (exact optimal).
    """
    n = len(jobs)
    T = get_time_horizon(jobs)

    # Sort jobs by deadline for consistency
    jobs = sorted(jobs, key=lambda x: x["d"])

    # DP dictionary: (index, used_slots) -> max profit
    from functools import lru_cache

    @lru_cache(None)
    def dp(i, used_mask):
        if i == n:
            return 0

        job = jobs[i]
        best = -10**9

        # Option 1: skip job → pay penalty
        skip_profit = -job["l"] + dp(i+1, used_mask)
        best = max(best, skip_profit)

        # Option 2: try to schedule job if enough slots available
        available_slots = [t for t in range(job["r"], job["d"]+1) if not (used_mask >> t) & 1]
        # available_slots = [t for t in range(job["r"], job["d"]) if not (used_mask >> t) & 1]

        if len(available_slots) >= job["p"]:
            # pick earliest p slots (any feasible subset works since only profit matters)
            new_mask = used_mask
            for t in available_slots[:job["p"]]:
                new_mask |= (1 << t)
            take_profit = job["w"] + dp(i+1, new_mask)
            best = max(best, take_profit)

        return best

    total_profit = dp(0, 0)

    # reconstruction
    assigned = {job["id"]: [] for job in jobs}
    status = {}

    def reconstruct(i, used_mask):
        if i == n:
            return
        job = jobs[i]
        skip_profit = -job["l"] + dp(i+1, used_mask)
        best = dp(i, used_mask)
        if best == skip_profit:
            status[job["id"]] = f"NOT done → -{job['l']}"
            reconstruct(i+1, used_mask)
            return
        # else scheduled
        available_slots = [t for t in range(job["r"], job["d"]+1) if not (used_mask >> t) & 1]
        new_mask = used_mask
        for t in available_slots[:job["p"]]:
            new_mask |= (1 << t)
            assigned[job["id"]].append(t)
        status[job["id"]] = f"DONE → +{job['w']}"
        reconstruct(i+1, new_mask)

    reconstruct(0, 0)

    # Pretty print results
    print("Schedule results:")
    for job in jobs:
        slots = assigned[job["id"]]
        print(f"Job {job['id']} {status[job['id']]}, slots = {slots if slots else 'null'}")
    print(f"\nTotal profit: {total_profit}")

    return assigned, total_profit



if __name__ == "__main__":
    jobs = read_jobs("test/test3.txt")
    assigned, profit = dp_schedule(jobs)