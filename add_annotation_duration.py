import sys
import csv
import datetime
from pathlib import Path

class excel_semicolon(csv.excel):
    delimiter = ';'

dataset = sys.argv[1]
filePath = sys.argv[2]

caseIdColName = "Case ID"
durationColName = "Duration"
timeStampColName = "Complete Timestamp"

dirPath = Path("/content/PRETSA/original_annotation/")
dirPath.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

# Define the output file path
writeFilePath = dirPath / f"{dataset}_duration.csv"

print(f"Writting: {writeFilePath}")

print(f"Reading: {filePath}")


with open(filePath) as csvfile:
    with open(writeFilePath,'w') as writeFile:
        reader = csv.DictReader(csvfile,delimiter=",")
        fieldNamesWrite = reader.fieldnames
        if (durationColName not in fieldNamesWrite):
            fieldNamesWrite.append(durationColName)
        writer = csv.DictWriter(writeFile, fieldnames=fieldNamesWrite,dialect=excel_semicolon)
        writer.writeheader()
        currentCase = ""
        for row in reader:
            if dataset != "bpic2017":
                formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']
                for fmt in formats:
                    try:
                        newTimeStamp = datetime.datetime.strptime(str(row[timeStampColName]), fmt)
                        break
                    except ValueError:
                        continue
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
