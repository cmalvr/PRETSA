import pandas as pd
from pathlib import Path
import numpy as np
import sys

t = sys.argv[1]


caseIDColName = "Case ID"

# Define directory for saving baseline logs
baseline_log_dir = Path("/content/PRETSA/baseline_event_logs_statistics")
baseline_log_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

dictPath = Path("/content/PRETSA/baselinelogs/")

datasets = ["CoSeLoG","Sepsis"]
df = pd.DataFrame(columns=['Dataset', 'k', 'method','variants','cases'])
for dataset in datasets:
    for k in (4, 8, 16):
        filePath = dictPath / f"{dataset}_pretsa_baseline_k{k}_t{t}.csv"
        eventLog = pd.read_csv(filePath, delimiter=";")
        number_variants = eventLog.Variant.value_counts()
        traces = eventLog[caseIDColName].value_counts()

        variants = eventLog.groupby('Variant')[caseIDColName].nunique(False)

        if len(traces) != 0:
            row = dict()
            row['Dataset'] = dataset
            row['k'] = k
            row['method'] = "baseline"
            row['variants'] = number_variants.size
            row['cases'] = len(traces)
            df = df._append(row,ignore_index=True)
csvPath = baseline_log_dir / "baseline_statistics.csv"
df.to_csv(sep=";",path_or_buf=csvPath)