import sys
from  pretsa_binary import Pretsa_binary
import pandas as pd
from pathlib import Path
import pickle
import time

dataset = sys.argv[1]
k = sys.argv[2]
t = sys.argv[3]

sys.setrecursionlimit(3000)

# Define annotation file path
annotationFilePath = f"/content/PRETSA/original_annotation/{dataset}_duration.csv"

# Read the event log
eventLog = pd.read_csv(annotationFilePath, delimiter=";")

# Define output directory
log_dir = Path("/content/PRETSA/pretsalog")
log_dir.mkdir(parents=True, exist_ok=True)

# Define output file paths
targetFilePath = log_dir / f"{dataset}_t{t}_k{k}_pretsa.csv"
targetFilePathPickle = log_dir / f"{dataset}_t{t}_k{k}_pretsa.pickle"

# Run PRETSA
print(f" Load Event Log: {annotationFilePath}")
start = time.time()
pretsa = Pretsa_binary(eventLog, dataset, t, k) #Initializing tree
cutOutCases, distanceLog = pretsa.runPretsa(int(k), float(t))

print(f" Modified {len(cutOutCases)} cases for k={k}, t={t}")
privateEventLog = pretsa.getPrivatisedEventLog()

# Save results (CSV + Pickle metadata)
privateEventLog.to_csv(targetFilePath, sep=";", index=False)
pickle.dump({"cases": cutOutCases, "inflictedChanges": distanceLog, "time": (time.time() - start)}, open(targetFilePathPickle, "wb"))

print(f" Private event log saved at: {targetFilePath}")
print(f" Experiment metadata saved at: {targetFilePathPickle}")