import subprocess

datasets = {
    "CoSeLoG": "/content/PRETSA/baselogs/CoSeLoG_dataset.csv",
    "Sepsis": "/content/PRETSA/baselogs/Sepsis_dataset.csv",
    "Road_Traffic_Fine_Management_Process": "/content/PRETSA/baselogs/traffic_fines_dataset.csv"
}

for dataset, filePath in datasets.items():
    for k in (4, 8, 16, 32, 64):
        t = 1.0
        subprocess.run(["python", "runExperimentForJournalExtension_pretsa.py", dataset, str(k), str(t)], check=True)