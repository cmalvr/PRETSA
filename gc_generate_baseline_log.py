import subprocess

datasets = {
    "CoSeLoG": "/content/PRETSA/original_annotation/CoSeLoG_duration.csv",
    "Sepsis": "/content/PRETSA/original_annotation/Sepsis_duration.csv",
    "Road_Traffic_Fine_Management_Process": "/content/PRETSA/original_annotation/Road_Traffic_Fine_Management_Process_duration.csv"
}

for dataset, filePath in datasets.items():
    for k in (4, 8, 16, 32, 64):
        t = 1.0
        subprocess.run(["python", "generate_baseline_log.py", filePath, dataset, str(k), str(t)], check=True)