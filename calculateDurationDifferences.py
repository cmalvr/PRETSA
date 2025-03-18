import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_duration_differences(original_file, sanitized_file):
    """
    Reads two CSV files (original and sanitized event logs), matches records by Activity and Case ID,
    and computes the absolute relative error between their durations.
    """
    # Load the CSV files
    original_df = pd.read_csv(original_file, delimiter=';')
    sanitized_df = pd.read_csv(sanitized_file, delimiter=';')
    
    # Ensure proper column names
    common_columns = ['Activity', 'Case ID', 'Duration']
    original_df = original_df[common_columns]
    sanitized_df = sanitized_df[common_columns]
    
    # Merge data on Activity and Case ID
    merged_df = original_df.merge(sanitized_df, on=['Activity', 'Case ID'], how='left', suffixes=('_orig', '_san'))

    # Fill missing durations in sanitized log with 0 (indicating removed activity)
    merged_df['Duration_san'] = merged_df['Duration_san'].fillna(0)
    
    # Compute absolute relative error
    merged_df['Relative Error'] = np.abs((merged_df['Duration_san'] - merged_df['Duration_orig']) / (merged_df['Duration_orig'] + 1e-6))
    
    return merged_df[['Activity', 'Case ID', 'Relative Error']]

def generate_heatmap(error_df, dataset_name):
    """
    Generates a heatmap of relative duration errors grouped by k-values and t-values.
    """
    pivot_table = error_df.pivot_table(values='Relative Error', index='t-value', columns='k-value', aggfunc='mean')
    
    plt.figure(figsize=(8, 5))
    sns.heatmap(pivot_table, cmap='hot_r', annot=True, fmt=".2f", linewidths=0.5)
    plt.xlabel('k-value')
    plt.ylabel('t-value')
    plt.title(f'Relative Error Heatmap ({dataset_name})')
    plt.show()
