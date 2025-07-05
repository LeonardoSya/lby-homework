import rasterio
import numpy as np
import matplotlib.pyplot as plt
import glob
from scipy.stats import linregress
import os

def main():
    """
    Analyzes a time series of phenology GeoTIFF files to calculate and
    visualize mean phenology and long-term trends.
    """
    # --- 1. Load Data ---
    data_dir = 'data/GEE_Phenology_Exports/'
    # Find all phenology tif files and sort them chronologically
    tif_files = sorted(glob.glob(os.path.join(data_dir, 'phenology_mentougou_*.tif')))

    if not tif_files:
        print(f"Error: No GeoTIFF files found in '{data_dir}'.")
        print("Please ensure your downloaded .tif files are in the correct directory.")
        return

    print(f"Found and loading {len(tif_files)} annual phenology files...")

    # Stack the rasters into a 3D numpy array (time, height, width)
    stack = []
    for f in tif_files:
        with rasterio.open(f) as src:
            # The exported bands are: 1=sos, 2=eos, 3=peak
            stack.append(src.read())
            profile = src.profile # Save the profile of the last file for writing output
    
    # stack is a list of (3, height, width) arrays. Convert to (time, band, height, width)
    phenology_stack = np.array(stack)
    
    # Separate the bands: SOS=0, EOS=1, Peak=2
    sos_ts = phenology_stack[:, 0, :, :]
    eos_ts = phenology_stack[:, 1, :, :]
    peak_ts = phenology_stack[:, 2, :, :]
    
    # Create a mask for valid data (e.g., ignore pixels where SOS is 0 or 1000)
    valid_mask = (sos_ts > 0) & (sos_ts < 366) & (eos_ts > 0) & (eos_ts < 366)
    
    # Apply mask to all time series
    sos_ts = np.where(valid_mask, sos_ts, np.nan)
    eos_ts = np.where(valid_mask, eos_ts, np.nan)
    peak_ts = np.where(valid_mask, peak_ts, np.nan)
    
    # --- 2. Calculate Mean Phenology ---
    print("Calculating mean phenology (2003-2023)...")
    mean_sos = np.nanmean(sos_ts, axis=0)
    mean_eos = np.nanmean(eos_ts, axis=0)
    mean_peak = np.nanmean(peak_ts, axis=0)
    
    # --- 3. Calculate Phenology Trends (per-pixel linear regression) ---
    print("Calculating phenology trends using linear regression...")
    years = np.arange(len(tif_files))
    
    # Get the dimensions
    _, height, width = sos_ts.shape
    
    # Create empty arrays to store trend results (slope)
    sos_slope = np.full((height, width), np.nan, dtype=np.float32)
    eos_slope = np.full((height, width), np.nan, dtype=np.float32)
    
    # Iterate over each pixel
    for r in range(height):
        for c in range(width):
            sos_pixel_series = sos_ts[:, r, c]
            eos_pixel_series = eos_ts[:, r, c]
            
            # Perform regression only if there are enough valid data points
            if np.count_nonzero(~np.isnan(sos_pixel_series)) > 5:
                sos_slope[r, c] = linregress(years, sos_pixel_series).slope
            
            if np.count_nonzero(~np.isnan(eos_pixel_series)) > 5:
                eos_slope[r, c] = linregress(years, eos_pixel_series).slope

    # Calculate Length of Season (LOS) trend
    los_slope = eos_slope - sos_slope

    # --- 4. Save Results as GeoTIFFs ---
    print("Saving analysis results as GeoTIFF files...")
    
    # Save Mean Phenology
    profile.update(count=3, dtype='float32', nodata=np.nan)
    with rasterio.open('phenology_mean_2003-2023.tif', 'w', **profile) as dst:
        dst.write(mean_sos.astype(np.float32), 1)
        dst.write(mean_eos.astype(np.float32), 2)
        dst.write(mean_peak.astype(np.float32), 3)
        dst.set_band_description(1, 'Mean_SOS_DOY')
        dst.set_band_description(2, 'Mean_EOS_DOY')
        dst.set_band_description(3, 'Mean_Peak_DOY')
    print("  - Saved phenology_mean_2003-2023.tif")

    # Save Phenology Trends
    with rasterio.open('phenology_trends_2003-2023.tif', 'w', **profile) as dst:
        dst.write(sos_slope, 1)
        dst.write(eos_slope, 2)
        dst.write(los_slope, 3)
        dst.set_band_description(1, 'SOS_Trend_days_per_year')
        dst.set_band_description(2, 'EOS_Trend_days_per_year')
        dst.set_band_description(3, 'LOS_Trend_days_per_year')
    print("  - Saved phenology_trends_2003-2023.tif")

    # --- 5. Visualize Results ---
    print("Generating result plots...")
    
    # Visualize Mean Phenology as RGB composite
    fig, ax = plt.subplots(figsize=(10, 10))
    # Normalize for visualization: R=EOS, G=LOS, B=SOS
    los_mean = mean_eos - mean_sos
    rgb_image = np.stack([
        (mean_eos - np.nanmin(mean_eos)) / (np.nanmax(mean_eos) - np.nanmin(mean_eos)),
        (los_mean - np.nanmin(los_mean)) / (np.nanmax(los_mean) - np.nanmin(los_mean)),
        (mean_sos - np.nanmin(mean_sos)) / (np.nanmax(mean_sos) - np.nanmin(mean_sos))
    ], axis=-1)
    ax.imshow(rgb_image)
    ax.set_title('Mean Phenology Composite (R=EOS, G=LOS, B=SOS)', fontsize=14)
    ax.set_axis_off()
    plt.savefig('phenology_mean_composite_plot.png', dpi=300, bbox_inches='tight')
    print("  - Saved phenology_mean_composite_plot.png")

    # Visualize Trends
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    trends = {'SOS Trend': sos_slope, 'EOS Trend': eos_slope, 'LOS Trend': los_slope}
    vm = 0.5 # Visual limit for color scale, days/year
    
    for i, (title, data) in enumerate(trends.items()):
        im = axes[i].imshow(data, cmap='RdBu_r', vmin=-vm, vmax=vm)
        axes[i].set_title(title, fontsize=14)
        axes[i].set_axis_off()
        fig.colorbar(im, ax=axes[i], orientation='horizontal', pad=0.05, label='Trend (days/year)')

    fig.suptitle('Phenology Trends (2003-2023)', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig('phenology_trends_plot.png', dpi=300, bbox_inches='tight')
    print("  - Saved phenology_trends_plot.png")

    plt.show()


if __name__ == '__main__':
    main() 