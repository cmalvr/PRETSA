import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

def generate_heatmap(dataset_name, option = "default"):
    """
    Generates a heatmap of relative duration errors grouped by k-values and t-values.

    Args:
        dataset_name (str): Name of the dataset (e.g., "CoSeLoG", "Sepsis").
    """

    # Define file path
    if option == "default":
        error_file = Path(f"/content/PRETSA/error_logs/{dataset_name}_duration_errors.csv")
    elif option == "binary":
        error_file = Path(f"/content/PRETSA/binary_error_logs/{dataset_name}_duration_errors.csv")

    # Load the error log
    if not error_file.exists():
        print(f"Error log not found: {error_file}")
        return

    error_df = pd.read_csv(error_file, delimiter=";")

    # Convert to float for calculations
    error_df['t-value'] = error_df['t-value'].astype(float)
    error_df['k-value'] = error_df['k-value'].astype(int)
    error_df['Relative Error'] = error_df['Relative Error'].astype(float)

    # Pivot table for heatmap (rows: t-values, cols: k-values)
    pivot_table = error_df.pivot_table(
        values='Relative Error',
        index='t-value',
        columns='k-value',
        aggfunc='mean'
    )

    # Generate heatmap
    plt.figure(figsize=(8, 5))
    sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap="YlOrRd", linewidths=0.5, cbar_kws={'label': 'Relative Error'})
    
    plt.title(f"Heatmap of Duration Errors ({dataset_name})")
    plt.xlabel("k-value")
    plt.ylabel("t-value")

    # Save heatmap
    heatmap_path = Path(f"/content/PRETSA/heatmaps/{dataset_name}_heatmap.png")
    heatmap_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(heatmap_path, dpi=300)
    
    print(f"Saved heatmap: {heatmap_path}")
    plt.show()