import sys
import subprocess

dictPath = sys.argv[1]

datasets = {
    "CoSeLoG": "/content/PRETSA/baselogs/CoSeLoG_dataset.csv",
    "Sepsis": "/content/PRETSA/baselogs/Sepsis_dataset.csv",
    "Road_Traffic_Fine_Management_Process": "/content/PRETSA/baselogs/traffic_fines_dataset.csv"
}

for dataset, filePath in datasets.items():
    for k in range(1,9):
        k = 2**k
        print(f"Processing: {dataset}")
        subprocess.run(["python", "add_annotation_duration.py", dataset, filePath, k], check=True)