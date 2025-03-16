import sys
import csv
import datetime
from pathlib import Path

class excel_semicolon(csv.excel):
    delimiter = ';'

dataset = sys.argv[1]
filePath = sys.argv[2]
k = int(sys.argv[3])

caseIdColName = "Case ID"
durationColName = "Duration"

dirPath = Path("/content/PRETSA/annotation/")
dirPath.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

# Define the output file path
writeFilePath = dirPath / f"{dataset}_duration_pretsa_baseline_k{str(k)}.csv"

print(writeFilePath)

timeStampColName = "Complete Timestamp"


with open(filePath) as csvfile:
    with open(writeFilePath,'w') as writeFile:
        reader = csv.DictReader(csvfile,delimiter=";")
        fieldNamesWrite = reader.fieldnames
        fieldNamesWrite.append(durationColName)
        writer = csv.DictWriter(writeFile, fieldnames=fieldNamesWrite,dialect=excel_semicolon)
        writer.writeheader()
        currentCase = ""
        for row in reader:
            if dataset != "bpic2017":
                newTimeStamp = datetime.datetime.strptime(row[timeStampColName], '%Y/%m/%d %H:%M:%S.%f')
                if currentCase != row[caseIdColName]:
                    currentCase = row[caseIdColName]
                    duration = 0.0
                else:
                    duration = (newTimeStamp - oldTimeStamp).total_seconds()
                oldTimeStamp = newTimeStamp
            else:
                startTimeStamp = datetime.datetime.strptime(row[timeStampColName], '%Y/%m/%d %H:%M:%S.%f')
                endTimeStamp = datetime.datetime.strptime(row[timeStampColName], '%Y/%m/%d %H:%M:%S.%f')
                duration = (endTimeStamp - startTimeStamp).total_seconds()
            row[durationColName] = duration
            writer.writerow(row)