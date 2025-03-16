import sys
import pandas as pd
from pathlib import Path


dictPath =  Path("/content/PRETSA/pretsalog")

caseIDColName = "Case ID"

#Ensure directory exists
baseline_log_dir = Path("/content/PRETSA/PRETSA_event_logs_statistics")
baseline_log_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

datasets = ["CoSeLoG", "Sepsis","Road_Traffic_Fine_Management_Process"]
df = pd.DataFrame(columns=['Dataset', 'k', 'method','variants','cases'])
for dataset in datasets:
    for k in (4,8,16):
        t = 1.0
        filePath = dictPath / f"{dataset}_t{t}_k{k}_pretsa.csv"
        eventLog = pd.read_csv(filePath, delimiter=";")
        variants = set()
        caseId = ""
        sequence = ""
        for ind in eventLog.index:

            if eventLog[caseIDColName][ind] != caseId:
                variants.add(sequence)
                caseId = eventLog[caseIDColName][ind]
                sequence = ""
            sequence += eventLog["Activity"][ind] + "@"

        traces = eventLog[caseIDColName].value_counts()

        if len(traces) != 0:
            row = dict()
            row['Dataset'] = dataset
            row['k'] = k
            row['method'] = "pretsa"
            row['variants'] = len(variants)
            row['cases'] = len(traces)
            print(row)
            df = df.append(row,ignore_index=True)
csvPath = dictPath + "pretsa_statistics.csv"
df.to_csv(sep=";",path_or_buf=csvPath)