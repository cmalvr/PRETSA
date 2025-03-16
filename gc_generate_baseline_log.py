import subprocess

datasets = {
    "CoSeLoG": "/content/PRETSA/original_annotation/CoSeLoG_duration.csv",
    "Sepsis": "/content/PRETSA/original_annotation/Sepsis_duration.csv"}

for dataset, filePath in datasets.items():
    for k in (4, 8, 16):
        t = 1.0
        cmd = ["python", "generate_baseline_log.py", filePath, dataset, str(k), str(t)]
        print(f"Running command: {' '.join(cmd)}")  # Debugging line
        subprocess.run(cmd, check=True)