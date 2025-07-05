import pandas as pd
import matplotlib.pyplot as plt
import pymannkendall as mk
import numpy as np

def main():
    """
    This script performs Mann-Kendall trend tests and calculates Sen's slope
    for annual NDVI data grouped by vegetation type.
    """
    # --- 1. Load and Prepare Data ---
    input_filename = 'data/zonal_ndvi_by_veg_type_mentougou.csv'
    try:
        df = pd.read_csv(input_filename)
    except FileNotFoundError:
        print(f"Error: Input file not found: '{input_filename}'")
        print("Please ensure you have downloaded the file to the 'project/data' directory.")
        return

    # IGBP Land Cover Legend to map IDs to readable names
    igbp_legend = {
      1: 'Evergreen Needleleaf Forest', 2: 'Evergreen Broadleaf Forest', 3: 'Deciduous Needleleaf Forest',
      4: 'Deciduous Broadleaf Forest', 5: 'Mixed Forest', 6: 'Closed Shrublands', 7: 'Open Shrublands',
      8: 'Woody Savannas', 9: 'Savannas', 10: 'Grasslands', 11: 'Permanent Wetlands', 12: 'Croplands',
      13: 'Urban and Built-up', 14: 'Cropland/Natural Vegetation Mosaic', 15: 'Snow and Ice', 16: 'Barren or Sparsely Vegetated',
      17: 'Water'
    }
    df['veg_type_name'] = df['veg_type_id'].map(igbp_legend)
    print("Successfully loaded and prepared data.")

    # --- 2. Perform Trend Analysis for Each Vegetation Type ---
    results = []
    # Get unique vegetation types present in the data, and sort them
    unique_veg_types = sorted(df['veg_type_id'].unique())

    print("\nPerforming trend analysis for each vegetation type...")
    for veg_id in unique_veg_types:
        veg_name = igbp_legend[veg_id]
        # Filter data for the current vegetation type and sort by year
        subset = df[df['veg_type_id'] == veg_id].sort_values('year')
        
        # Check if there's enough data to perform the test
        if len(subset) < 4: # MK test requires at least 4 data points
            print(f"Skipping '{veg_name}': Not enough data points.")
            continue

        # Perform the Mann-Kendall test
        result = mk.original_test(subset['mean_ndvi'])
        
        results.append({
            'Vegetation Type': veg_name,
            'Trend': result.trend,
            'p-value': f"{result.p:.4f}",
            'Sen\'s Slope': f"{result.slope:.6f}",
            'Significant (p<0.05)': 'Yes' if result.p < 0.05 else 'No'
        })

    # Convert results to a DataFrame for pretty printing
    results_df = pd.DataFrame(results)

    # --- 3. Display and Save Results Table ---
    print("\n--- Trend Analysis Results ---")
    print(results_df.to_string())
    
    # Save the results table to a CSV file
    results_filename = 'ndvi_trend_analysis_results.csv'
    results_df.to_csv(results_filename, index=False)
    print(f"\nResults table saved to '{results_filename}'")
    
    # --- 4. Visualize the Results ---
    print("Generating results plot...")
    
    # Prepare data for plotting
    plot_df = results_df.copy()
    plot_df["Sen's Slope"] = pd.to_numeric(plot_df["Sen's Slope"])
    plot_df = plot_df.sort_values("Sen's Slope", ascending=False)

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create the bar plot
    bars = ax.bar(plot_df['Vegetation Type'], plot_df["Sen's Slope"], color='skyblue')
    
    # Add significance asterisks
    for i, (idx, row) in enumerate(plot_df.iterrows()):
        if row['Significant (p<0.05)'] == 'Yes':
            y_pos = row["Sen's Slope"]
            # Adjust y position for visual clarity
            offset = 0.0001 if y_pos >= 0 else -0.0003
            ax.text(i, y_pos + offset, '*', ha='center', va='bottom', fontsize=20, color='red')

    # Formatting the plot
    ax.set_title('Annual NDVI Trend by Vegetation Type (2003-2023)', fontsize=16)
    ax.set_ylabel("Sen's Slope (Annual Change in NDVI)", fontsize=12)
    ax.set_xlabel("Vegetation Type", fontsize=12)
    plt.xticks(rotation=45, ha='right') # Rotate labels for better readability
    ax.axhline(0, color='grey', lw=1) # Add a zero line for reference
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    fig.tight_layout()

    # Save the plot
    plot_filename = 'ndvi_trend_analysis_plot.png'
    plt.savefig(plot_filename, dpi=300)
    print(f"Results plot saved to '{plot_filename}'")

    # Show the plot
    plt.show()

if __name__ == '__main__':
    main() 