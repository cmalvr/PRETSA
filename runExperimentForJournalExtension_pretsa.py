import sys
import subprocess

dataset = sys.argv[1]
k = sys.argv[2]
t = sys.argv[3]

# Run runPretsa.py to process the dataset
subprocess.run(["python", "runPretsa.py", dataset, str(k), str(t)], check=True)