import sys
import pandas as pd
import csv
from pathlib import Path

class excel_semicolon(csv.excel):
    delimiter = ';'

baseline_log_dir = Path("/content/PRETSA/original_event_log_annotations/")
baseline_log_dir.mkdir(parents=True, exist_ok=True) 
writeFilePath = baseline_log_dir / "original_annotations.csv"


dictPath = Path("/content/PRETSA/original_annotation/")

with open(writeFilePath, 'w+') as writeFile:
    fieldNamesWrite = ["Event Log","method","activity","Avg. Duration"]
    writer = csv.DictWriter(writeFile, fieldnames=fieldNamesWrite, dialect=excel_semicolon)
    writer.writeheader()
    for dataset in ["CoSeLoG","Sepsis","Road_Traffic_Fine_Management_Process"]:
        filePath = dictPath / f"{dataset}_duration.csv"
        eventLog = pd.read_csv(filePath, delimiter=";")
        data = eventLog.groupby('Activity').Duration.agg("mean")
        for row in data.items():
            (key, value) = row
            line = dict()
            line["Event Log"] = dataset
            line["method"] = "original"
            line["activity"] = key
            line["Avg. Duration"] = value
            writer.writerow(line)

