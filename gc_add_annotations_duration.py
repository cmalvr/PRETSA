import sys
import subprocess


datasets = {
    "CoSeLoG": "/content/PRETSA/baselogs/CoSeLoG_dataset.csv",
    "Sepsis": "/content/PRETSA/baselogs/Sepsis_dataset.csv",
    "Road_Traffic_Fine_Management_Process": "/content/PRETSA/baselogs/traffic_fines_dataset.csv"
}

for dataset, filePath in datasets.items():
    print(f"Processing: {dataset}")
    for k in range(1, 9):
        k = str(2**k)  # Convert k to string
        subprocess.run(["python", "add_annotation_duration.py", dataset, filePath], check=True)