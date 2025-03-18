import pandas as pd
import csv
import os
import numpy as np
from pathlib import Path
import sys

t = sys.argv[1]

class excel_semicolon(csv.excel):
    delimiter = ';'

dictPath = Path("/content/PRETSA/pretsalog")

logPath = Path("/content/PRETSA/PRETSA_event_log_annotations/")
logPath.mkdir(parents=True, exist_ok=True) 

writeFilePath = logPath / "pretsa_annotations.csv"

with open(writeFilePath, 'w+') as writeFile:
    caseIDColName = "Case ID"
    datasets = ["CoSeLoG","Sepsis"]
    fieldNamesWrite = ["Event Log","k","t","method","activity","Avg. Duration"]
    writer = csv.DictWriter(writeFile, fieldnames=fieldNamesWrite, dialect=excel_semicolon)
    writer.writeheader()
    for dataset in datasets:
        for k in (4,8,16):
            filePath = dictPath / f"{dataset}_t{t}_k{k}_pretsa.csv"
            if os.path.isfile(filePath):
                eventLog = pd.read_csv(filePath, delimiter=";")
                eventLog = eventLog.replace(-1.0,np.nan)
                if not eventLog.empty:
                    data = eventLog.groupby('Activity').Duration.agg("mean")
                    for row in data.items():
                        (key, value) = row
                        line = dict()
                        line["Event Log"] = dataset
                        line["k"] = k
                        line["t"] = str(t)
                        line["method"] = "pretsa"
                        line["activity"] = key
                        line["Avg. Duration"] = value
                        writer.writerow(line)
            else:
                print(filePath + " does not exist")