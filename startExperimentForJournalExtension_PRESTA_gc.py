import pretsa
import subprocess
import sys
from pathlib import Path

file_path = Path(sys.argv[1])  # Convert to Path object
file_name = file_path.name  # Extract only the file name

for k in (4, 8, 16, 32, 64):
    t = 1.0  # Keeping t fixed at 1.0

    # Log file using only the file name (without the path)
    log_file = f"log_{file_name}_k{k}.txt"

    # Run experiment and redirect output to log files
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            ["python", "runExperimentForJournalExtension_pretsa.py", str(file_path), str(k), str(t)],
            stdout=log, stderr=log, text=True
        )

    print(f"Started experiment for k={k}, logs -> {log_file}")