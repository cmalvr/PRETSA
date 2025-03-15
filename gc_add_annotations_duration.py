import sys
import subprocess

dictPath = sys.argv[1]

datasets = ["CoSeLoG", "Sepsis", "Road_Traffic_Fine_Management_Process"]
for dataset in datasets:
    print(dataset)
    for k in range(1, 9):
        k = 2**k
        filePath = f"{dictPath}{dataset}_duration_pretsa_baseline_k{k}.csv"
        subprocess.run(["python", "add_annotation_duration.py", "normal", filePath], check=True)