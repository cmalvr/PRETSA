import sys
from pretsa import Pretsa
import pandas as pd
from pathlib import Path

filePath = Path(sys.argv[1])
k = sys.argv[2] 
t = sys.argv[3]  

sys.setrecursionlimit(3000)

# Define output directory for Pretsa logs
log_dir = Path("/content/PRETSA/pretsalog")
log_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

# Define output file path in the pretsalog directory
targetFilePath = log_dir / filePath.name.replace(".csv", f"_t{t}_k{k}_pretsa.csv")

# Start processing
print(f" Load Event Log: {filePath}")
eventLog = pd.read_csv(filePath, delimiter=";")

print("Starting experiments")
pretsa = Pretsa(eventLog)
cutOutCases = pretsa.runPretsa(int(k), float(t))

print(f" Modified {len(cutOutCases)} cases for k={k}, t={t}")
privateEventLog = pretsa.getPrivatisedEventLog()

privateEventLog.to_csv(targetFilePath, sep=";", index=False)
print(f" Private event log saved at: {targetFilePath}")
