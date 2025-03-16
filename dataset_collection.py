import requests
import pm4py
import pandas as pd
import gzip
from pathlib import Path

# Dictionary of datasets with their URLs
datasets = {
    "CoSeLoG": "https://data.4tu.nl/file/2db2e3c1-9499-4699-9098-1a28c15a5913/21758246-61e7-4019-bf7d-fb6a9b38df14", 
    "Sepsis": "https://data.4tu.nl/file/33632f3c-5c48-40cf-8d8f-2db57f5a6ce7/643dccf2-985a-459e-835c-a82bce1c0339", 
    "Road_Traffic_Fine_Management_Process": "https://data.4tu.nl/file/806acd1a-2bf2-4e39-be21-69b8cad10909/b234b06c-4d4f-4055-9f14-6218e3906d82" 
}
# Define directory for downloads and conversions
download_dir = Path("downloads")
csv_dir = Path("csv_outputs")
download_dir.mkdir(parents=True, exist_ok=True)
csv_dir.mkdir(parents=True, exist_ok=True)

for dataset, url in datasets.items():
    xes_gz_path = download_dir / f"{dataset}.xes.gz"
    csv_output_path = csv_dir / f"{dataset}_dataset.csv"

    # Step 1: Download file
    print(f"Downloading {dataset} from {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(xes_gz_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print(f"Downloaded: {xes_gz_path}")
    else:
        print(f"Failed to download {dataset} - HTTP {response.status_code}")
        continue

    # Step 2: Convert XES to CSV
    print(f"Processing {dataset}...")
    log = pm4py.read_xes(str(xes_gz_path))
    df = pm4py.convert_to_dataframe(log)
    df.to_csv(csv_output_path, index=False)
    print(f"Saved CSV: {csv_output_path}")

print("All datasets processed.")