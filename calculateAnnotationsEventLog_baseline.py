import sys
import pandas as pd
import csv
from pathlib import Path
import os

class excel_semicolon(csv.excel):
    delimiter = ';'

baseline_log_dir = Path("/content/PRETSA/baseline_event_log_annotations/")
baseline_log_dir.mkdir(parents=True, exist_ok=True) 

writeFilePath = baseline_log_dir / "baseline_annotations.csv"


dictPath = "/content/PRETSA/baselinelogs/"

with open(writeFilePath, 'w+') as writeFile:
    caseIDColName = "Case ID"
    datasets = ["Road_Traffic_Fine_Management_Process","CoSeLoG","Sepsis"]
    fieldNamesWrite = ["Event Log","k","t","method","activity","Avg. Duration"]
    writer = csv.DictWriter(writeFile, fieldnames=fieldNamesWrite, dialect=excel_semicolon)
    writer.writeheader()
    for dataset in datasets:
        for k in (4, 8, 16):
            t = 1.0
            filePath = dictPath / f"{dataset}_pretsa_baseline_k{k}_t{t}.csv"
            if os.path.isfile(filePath):
                eventLog = pd.read_csv(filePath, delimiter=";")
                if not eventLog.empty:
                    data = eventLog.groupby('Activity').Duration.agg("mean")
                    for row in data.iteritems():
                        (key, value) = row
                        line = dict()
                        line["Event Log"] = dataset
                        line["k"] = k
                        line["t"] = t
                        line["method"] = "pretsa_baseline"
                        line["activity"] = key
                        line["Avg. Duration"] = value
                        writer.writerow(line)
            else:
                print(filePath + "does not exist")