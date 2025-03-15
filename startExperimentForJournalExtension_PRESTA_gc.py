import subprocess
import sys
from pathlib import Path

# Get the input file path and name
file_path = Path(sys.argv[1])
file_name = file_path.name  # Extract only the file name

# Define the log directory
log_dir = Path("/content/PRETSA/runlogs")
log_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

for k in (4, 8, 16, 32, 64):
    t = 1.0  # Keeping t fixed at 1.0

    # Define log file path inside the runlogs directory
    log_file = log_dir / f"log_{file_name}_k{k}.txt"

    # Run experiment and redirect output to log files
    with open(log_file, "w") as log:
        process = subprocess.Popen(
            ["python", "runExperimentForJournalExtension_pretsa.py", str(file_path), str(k), str(t)],
            stdout=log, stderr=log, text=True
        )

    print(f"Started experiment for k={k}, logs -> {log_file}")
