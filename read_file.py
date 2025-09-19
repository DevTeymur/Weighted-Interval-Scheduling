def read_jobs(filename):
    jobs = []
    with open(filename, "r") as f:
        n = int(f.readline().strip())   # number of jobs
        for j in range(n):
            line = f.readline().strip()
            r, d, p, w, l = map(int, line.split(","))
            jobs.append({
                "id": j+1,
                "r": r,
                "d": d,
                "p": p,
                "w": w,
                "l": l
            })
    return jobs


if __name__ == "__main__":
    filename = "test/test4.txt"
    jobs = read_jobs(filename)
    for job in jobs:
        print(job)