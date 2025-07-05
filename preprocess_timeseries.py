import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import numpy as np

def main():
    """
    This script loads the merged time series data, performs preprocessing
    (interpolation and smoothing), and visualizes the results.
    """
    # --- 1. Load Data ---
    input_filename = 'mentougou_vegetation_indices_2003-2023.csv'
    try:
        df = pd.read_csv(input_filename, parse_dates=['date'])
    except FileNotFoundError:
        print(f"Error: Input file not found: '{input_filename}'")
        print("Please ensure the script is run from the 'project' directory and the file exists.")
        return

    print("Successfully loaded data.")
    
    # --- 2. Preprocessing ---
    
    param_cols = ['NDVI', 'GPP', 'EVI', 'LAI']
    
    # Handle missing values - particularly for GPP
    # We use linear interpolation to fill the gaps.
    for col in param_cols:
        if df[col].isnull().any():
            print(f"Found missing values in '{col}'. Applying linear interpolation.")
            df[col] = df[col].interpolate(method='linear', limit_direction='both')

    # Apply Savitzky-Golay (SG) filter for smoothing
    # window_length: The number of data points to use in the filter window. Must be odd.
    # polyorder: The order of the polynomial used to fit the samples.
    # These values are typical for monthly remote sensing data.
    window_length = 7
    polyorder = 3
    
    print(f"Applying Savitzky-Golay filter with window={window_length}, polyorder={polyorder}")
    
    for col in param_cols:
        df[f'{col}_smoothed'] = savgol_filter(df[col], window_length, polyorder)
        # Ensure smoothed values are not physically implausible (e.g., negative NDVI)
        if col in ['NDVI', 'EVI']:
             df[f'{col}_smoothed'] = df[f'{col}_smoothed'].clip(0, 1)
        else:
             df[f'{col}_smoothed'] = df[f'{col}_smoothed'].clip(0)


    # --- 3. Save the Preprocessed Data ---
    output_filename = 'mentougou_vegetation_indices_preprocessed.csv'
    df.to_csv(output_filename, index=False)
    print(f"\\nSuccessfully preprocessed data and saved to '{output_filename}'")

    # --- 4. Visualize the Results ---
    print("Generating comparison plot...")
    
    # Create a 2x2 subplot layout
    fig, axes = plt.subplots(2, 2, figsize=(18, 10), sharex=True)
    fig.suptitle('Comparison of Original vs. Smoothed Vegetation Indices', fontsize=16)
    
    # Flatten axes array for easy iteration
    axes = axes.flatten()
    
    for i, col in enumerate(param_cols):
        ax = axes[i]
        # Plot original data as a thin, semi-transparent line
        ax.plot(df['date'], df[col], label='Original', color='gray', alpha=0.6, lw=1.5)
        # Plot smoothed data as a thicker, solid line
        ax.plot(df['date'], df[f'{col}_smoothed'], label='Smoothed (SG Filter)', color='blue', lw=2)
        
        ax.set_title(col, fontsize=14)
        ax.set_ylabel('Index Value')
        ax.legend()
        ax.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout to make room for suptitle

    # Save the plot to a file
    plot_filename = 'mentougou_indices_smoothing_comparison.png'
    plt.savefig(plot_filename, dpi=300)
    print(f"Comparison plot saved to '{plot_filename}'")
    
    # Show the plot
    plt.show()

if __name__ == '__main__':
    main() 