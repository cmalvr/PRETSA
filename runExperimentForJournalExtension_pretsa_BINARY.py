import sys
import subprocess

dataset = sys.argv[1]
k = sys.argv[2]
t = sys.argv[3]

# Run runPretsa.py to process the dataset
subprocess.run(["python", "/content/PRETSA/runPretsa_BINARY.py", dataset, str(k), str(t)], check=True)