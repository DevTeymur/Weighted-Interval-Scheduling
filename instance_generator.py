
import random
import os
import zipfile

# Create directory to hold instances
output_dir = "job_scheduling_instances"
os.makedirs(output_dir, exist_ok=True)

# Configuration
num_instances = 1000
min_jobs = 2
max_jobs = 19
min_time_slot = 1
max_time_slot = 100

for instance_id in range(1, num_instances + 1):
    n = random.randint(min_jobs, max_jobs)
    lines = [str(n)]
    
    for _ in range(n):
        rj = random.randint(min_time_slot, max_time_slot - 10)
        pj = random.randint(1, 10)
        dj = random.randint(rj + pj, rj + pj + 20)
        wj = random.randint(10, 100)
        lj = random.randint(5, 50)
        
        line = f"{rj},{dj},{pj},{wj},{lj}"
        lines.append(line)
    
    filename = f"instance_{instance_id:04d}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        f.write("\n".join(lines))

# Zip all files
zip_filename = "job_scheduling_instances.zip"
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, _, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, output_dir)
            zipf.write(file_path, arcname)

print(f"All {num_instances} instances generated and zipped as '{zip_filename}'.")