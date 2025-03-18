import subprocess
import sys

t = sys.argv[1]

print(t)

datasets = {
    "CoSeLoG",
    "Sepsis"
}

for dataset in datasets:
    for k in (4, 8, 16):
        subprocess.run(["python", "/content/PRETSA/runExperimentForJournalExtension_pretsa.py", dataset, str(k), str(t)], check=True)