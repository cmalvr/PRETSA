import os
import pandas as pd
import re
from pathlib import Path

def extract_t_k_values(filename):
    """Extracts t and k values from filenames like 'CoSeLoG_t0.1_k16_pretsa.csv'."""
    match = re.search(r"_t([\d\.]+)_k(\d+)_pretsa\.csv", filename)
    if match:
        t_value = float(match.group(1))
        k_value = int(match.group(2))
        return t_value, k_value
    return None, None

def find_matching_files(dataset_name, option = "default"):
    """Finds matching original (sanitized) and processed (original) files based on t and k values."""
    original_dir = "/content/PRETSA/original_annotation/"
    if option == "default":
        sanitized_dir = "/content/PRETSA/pretsalog/"
    elif option == "binary":
        sanitized_dir = "/content/PRETSA/pretsa_binarylog/"

    # List files in directories
    original_files = [f for f in os.listdir(original_dir) if dataset_name in f]
    sanitized_files = [f for f in os.listdir(sanitized_dir) if dataset_name in f]

    # Match files by extracting t and k values
    matches = []
    for sanitized_file in sanitized_files:
        t, k = extract_t_k_values(sanitized_file)
        if t is not None and k is not None:
            for original_file in original_files:
                if original_file.startswith(f"{dataset_name}_duration"):
                    matches.append((os.path.join(original_dir, original_file), 
                                    os.path.join(sanitized_dir, sanitized_file),
                                    t, k))
    return matches

def calculate_duration_differences(dataset_name, option = "default"):
    """Calculates duration differences for all matched files of a dataset."""
    matches = find_matching_files(dataset_name, option)
    if not matches:
        print(f"No matching files found for dataset: {dataset_name}")
        return None

    error_logs = []

    for original_file, sanitized_file, t, k in matches:
        print(f"Processing {original_file} and {sanitized_file} for t={t}, k={k}")

        # Load CSV files
        original_df = pd.read_csv(original_file, delimiter=";")
        sanitized_df = pd.read_csv(sanitized_file, delimiter=";")

        # Merge data on Activity and Case ID
        merged_df = original_df.merge(sanitized_df, on=['Activity', 'Case ID'], how='left', suffixes=('_orig', '_san'))

        # Ensure missing durations in sanitized dataset are set to zero
        merged_df['Duration_san'] = merged_df['Duration_san'].fillna(0)

        # Compute relative error
        merged_df['Relative Error'] = merged_df.apply(
            lambda row: abs((row['Duration_san'] / row['Duration_orig']) - 1.0) if row['Duration_orig'] != 0 else 0,
            axis=1
        )

        # Add t and k values for grouping
        merged_df['t-value'] = t
        merged_df['k-value'] = k

        # Store results
        error_logs.append(merged_df[['Activity', 'Case ID', 'Duration_orig', 'Duration_san', 'Relative Error', 't-value', 'k-value']])

    # Concatenate all logs
    if error_logs:
        final_df = pd.concat(error_logs, ignore_index=True)

        # Save results
        if option == "default":
            output_dir = Path("/content/PRETSA/error_logs/")
            output_dir.mkdir(parents=True, exist_ok=True)
        elif option == "binary":
            output_dir = Path("/content/PRETSA/binary_error_logs/")
            output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{dataset_name}_duration_errors.csv"
        final_df.to_csv(output_path, sep=";", index=False)

        print(f"Saved error log: {output_path}")
        return final_df

    return None