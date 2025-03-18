import subprocess
import sys
import json

k_value = json.loads(sys.argv[1])
t_value = json.loads(sys.argv[2])

datasets = {
    "CoSeLoG",
    "Sepsis"
}

for dataset in datasets:
    for k in k_value:
        for t in t_value:
            subprocess.run(["python", "/content/PRETSA/runExperimentForJournalExtension_pretsa.py", dataset, str(k), str(t)], check=True)