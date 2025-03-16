import sys
import pandas as pd
import csv
from statistics import mean
from pathlib import Path

class excel_semicolon(csv.excel):
    delimiter = ';'

dictFiles = {"baseline":"/content/PRETSA/baseline_event_log_annotations/baseline_annotations.csv",
             "pretsa":"/content/PRETSA/PRETSA_event_log_annotations/pretsa_statistics_annotations.csv"}
fileOriginalDataPath = "/content/PRETSA/original_event_log_annotations/original_annotations.csv"



originalData = pd.read_csv(fileOriginalDataPath, delimiter=";")
originalDataDict = dict()
for index, row in originalData.iterrows():
    activityDict = originalDataDict.get(row["Event Log"],dict())
    activityDict[row["activity"]] = row["Avg. Duration"]
    originalDataDict[row["Event Log"]] = activityDict

logPath = Path("/content/PRETSA/AnnotationError")
logPath.mkdir(parents=True, exist_ok=True) 

writeFilePath = logPath / "pretsa_annotation_errors.csv"


with open(writeFilePath, 'w+') as writeFile:
    fieldNamesWrite = ["Event Log","method","k","t","activity","Relative Error"]
    writer = csv.DictWriter(writeFile, fieldnames=fieldNamesWrite, dialect=excel_semicolon)
    writer.writeheader()
    for method, filePath in dictFiles.items():
        algorithmData = pd.read_csv(filePath, delimiter=";")
        for k in range(4,8,16):
            t = 1.0
            for dataset in ["Sepsis","CoSeLoG","Road_Traffic_Fine_Management_Process"]:
                currentSlide = algorithmData.loc[(algorithmData["k"] == k) & (algorithmData["t"] == t) & (algorithmData["Event Log"] == dataset)]
                currentSlideDict = dict()
                for index, rowInSlide in currentSlide.iterrows():
                    currentSlideDict[rowInSlide["activity"]] = rowInSlide["Avg. Duration"]
                errorList = []
                for activity in originalDataDict[dataset].keys():
                    originalValue = originalDataDict[dataset][activity]
                    if originalValue != 0.0:
                        algorithmValue = currentSlideDict.get(activity,0.0)
                        relativeError = abs((algorithmValue/originalValue) - 1.0)
                        csvRow ={}
                        csvRow["Event Log"] = dataset
                        csvRow["method"] = method
                        csvRow["k"] = k
                        csvRow["t"] = t
                        csvRow["activity"] = activity
                        csvRow["Relative Error"] = relativeError
                        writer.writerow(csvRow)
                        errorList.append(relativeError)
                csvRow = {}
                csvRow["Event Log"] = dataset
                csvRow["method"] = method
                csvRow["k"] = k
                csvRow["t"] = t
                csvRow["activity"] = "Average Activites"
                csvRow["Relative Error"] = mean(errorList)
                writer.writerow(csvRow)










