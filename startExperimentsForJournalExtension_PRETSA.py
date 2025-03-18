import subprocess
import sys

t = float(sys.argv[1])

datasets = {
    "CoSeLoG",
    "Sepsis"
}

for dataset in datasets:
    for k in (4, 8, 16):
        subprocess.run(["python", "/content/PRETSA/runExperimentForJournalExtension_pretsa.py", dataset, str(k), str(t)], check=True)