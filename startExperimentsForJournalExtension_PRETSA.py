import subprocess

datasets = {
    "CoSeLoG",
    "Sepsis"
}

for dataset in datasets:
    for k in (4, 8, 16):
        t = 1.0
        subprocess.run(["python", "/content/PRETSA/runExperimentForJournalExtension_pretsa.py", dataset, str(k), str(t)], check=True)