import pandas as pd
import matplotlib.pyplot as plt
import glob
from functools import reduce
import os

def main():
    """
    This script loads the downloaded vegetation index data from GEE,
    merges them into a single time series, saves the result, and
    creates a visualization.
    """
    # --- 1. Load and Merge Data ---

    # Use glob to find all the downloaded CSV files in the 'data' subdirectory.
    # Assumes the script is run from inside the 'project' directory.
    csv_files = glob.glob('data/*_mentougou_monthly.csv')
    
    if not csv_files:
        print("Error: No CSV files found.")
        print("Please make sure you have downloaded the CSV files from Google Drive")
        print("and placed them in the 'project/data' directory where this script is located.")
        return

    print(f"Found {len(csv_files)} files to process: {csv_files}")

    # Read each CSV into a pandas DataFrame
    data_frames = []
    for f in csv_files:
        # Get the filename from the path and then extract the parameter name
        param_name = os.path.basename(f).split('_')[0] # e.g., 'NDVI' from 'NDVI_mentougou_monthly.csv'
        df = pd.read_csv(f)
        # Drop the unnecessary columns and rename the value column to its parameter name
        df = df.drop(columns=['system:index', '.geo'])
        df = df.rename(columns={param_name: param_name}) # Ensure column name is correct
        data_frames.append(df)

    # Merge all dataframes together on 'year' and 'month'
    # Start with the first dataframe and iteratively merge the rest
    merged_df = reduce(lambda left, right: pd.merge(left, right, on=['year', 'month'], how='outer'), data_frames)

    # --- 2. Clean and Format Data ---

    # Create a 'date' column for proper time series plotting
    merged_df['date'] = pd.to_datetime(merged_df['year'].astype(int).astype(str) + '-' + merged_df['month'].astype(int).astype(str) + '-01')
    
    # Sort the dataframe by date
    merged_df = merged_df.sort_values('date').reset_index(drop=True)

    # Reorder columns to be more intuitive
    param_cols = [col for col in merged_df.columns if col not in ['system:index', '.geo', 'year', 'month', 'date']]
    final_cols = ['date', 'year', 'month'] + param_cols
    merged_df = merged_df[final_cols]
    
    # --- 3. Save the Combined Data ---
    output_filename = 'mentougou_vegetation_indices_2003-2023.csv'
    merged_df.to_csv(output_filename, index=False)
    print(f"\\nSuccessfully merged data and saved to '{output_filename}'")
    
    # Display summary statistics
    print("\\nSummary Statistics of the Merged Data:")
    print(merged_df.describe())

    # --- 4. Visualize the Data ---
    
    print("\\nGenerating plot...")
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(15, 8))

    for param in param_cols:
        ax.plot(merged_df['date'], merged_df[param], label=param, lw=2)

    # Formatting the plot
    ax.set_title('Monthly Vegetation Indices for Mentougou Area (2003-2023)', fontsize=16)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Index Value', fontsize=12)
    ax.legend(title='Vegetation Index', fontsize=10)
    ax.grid(True)
    fig.tight_layout()

    # Save the plot to a file
    plot_filename = 'mentougou_vegetation_indices_timeseries.png'
    plt.savefig(plot_filename, dpi=300)
    print(f"Plot saved to '{plot_filename}'")
    
    # Show the plot
    plt.show()


if __name__ == '__main__':
    main() 