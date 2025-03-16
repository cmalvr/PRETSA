import sys
import subprocess


datasets = {
    "CoSeLoG": "/content/PRETSA/csv_outputs/CoSeLoG_dataset.csv",
    "Sepsis": "/content/PRETSA/csv_outputs/Sepsis_dataset.csv"
}

for dataset, filePath in datasets.items():
    print(f"Processing: {dataset}")
    subprocess.run(["python", "/content/PRETSA/add_annotation_duration.py", dataset, filePath], check=True)