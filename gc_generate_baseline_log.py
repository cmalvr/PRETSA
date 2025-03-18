import subprocess
import sys

t = sys.argv[1]

datasets = {
    "CoSeLoG": "/content/PRETSA/original_annotation/CoSeLoG_duration.csv",
    "Sepsis": "/content/PRETSA/original_annotation/Sepsis_duration.csv"}

for dataset, filePath in datasets.items():
    for k in (4, 8, 16):
        subprocess.run(["python", "generate_baseline_log.py", filePath, dataset, str(k), str(t)], check=True)