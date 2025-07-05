import rasterio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from rasterio.enums import Resampling

# Define the IGBP land cover class names based on MODIS MCD12Q1 documentation
IGBP_CLASSIFICATION = {
    1: 'Evergreen Needleleaf Forests',
    2: 'Evergreen Broadleaf Forests',
    3: 'Deciduous Needleleaf Forests',
    4: 'Deciduous Broadleaf Forests',
    5: 'Mixed Forests',
    6: 'Closed Shrublands',
    7: 'Open Shrublands',
    8: 'Woody Savannas',
    9: 'Savannas',
    10: 'Grasslands',
    11: 'Permanent Wetlands',
    12: 'Croplands',
    13: 'Urban and Built-up Lands',
    14: 'Cropland/Natural Vegetation Mosaics',
    15: 'Permanent Snow and Ice',
    16: 'Barren',
    17: 'Water Bodies'
}

def main():
    """
    Performs zonal statistics using rasterio and pandas to calculate the mean 
    phenology trend for each land cover type and visualizes the results.
    """
    # --- 1. Define Input File Paths ---
    landcover_path = 'data/landcover_mentougou_2013.tif'
    trends_path = 'phenology_trends_2003-2023.tif'
    output_csv = 'phenology_trends_by_vegetation.csv'
    output_plot = 'phenology_trends_by_vegetation_plot.png'

    print("Starting zonal statistics using a manual numpy/pandas approach...")

    # --- 2. Load Raster Data and Ensure Alignment ---
    # First, open the trends raster to use as the reference grid
    with rasterio.open(trends_path) as src:
        trends_profile = src.profile
        sos_trend_array = src.read(1)
        eos_trend_array = src.read(2)
        los_trend_array = src.read(3)
        trend_nodata = src.nodata

    # Now, open the landcover raster and resample it on-the-fly to match the trends grid
    with rasterio.open(landcover_path) as src:
        landcover_array = src.read(
            1,
            out_shape=(trends_profile['height'], trends_profile['width']),
            resampling=Resampling.nearest
        )
        lc_nodata = src.nodata

    # --- 3. Create a Pandas DataFrame from the now-aligned arrays ---
    # Flatten arrays to create 1D arrays (series) of pixels
    lc_flat = landcover_array.flatten()
    sos_flat = sos_trend_array.flatten()
    eos_flat = eos_trend_array.flatten()
    los_flat = los_trend_array.flatten()

    # Create DataFrame
    df = pd.DataFrame({
        'LC_Type_ID': lc_flat,
        'SOS_Trend': sos_flat,
        'EOS_Trend': eos_flat,
        'LOS_Trend': los_flat,
    })

    # --- 4. Clean and Process Data ---
    # Remove NoData pixels from both rasters
    # A pixel is invalid if it's nodata in *either* the landcover or the trend raster.
    if lc_nodata is not None:
        df = df[df['LC_Type_ID'] != lc_nodata]
    if trend_nodata is not None:
        df = df[~np.isnan(df['SOS_Trend'])] # Assuming trend nodata is NaN

    # Filter out non-vegetation classes we don't want to analyze
    df = df[~df['LC_Type_ID'].isin([0, 13, 15, 16, 17])]
    
    # Drop rows with any remaining NaN values
    df.dropna(inplace=True)
    
    if df.empty:
        print("Error: DataFrame is empty after cleaning. No valid overlapping data found.")
        print("Please check that your landcover and trend rasters align and have valid data.")
        return

    # --- 5. Group by Land Cover and Calculate Mean ---
    zonal_mean = df.groupby('LC_Type_ID').mean()
    zonal_mean['Vegetation_Type'] = zonal_mean.index.map(IGBP_CLASSIFICATION)
    zonal_mean.rename(columns={
        'SOS_Trend': 'SOS_Trend_days_per_year',
        'EOS_Trend': 'EOS_Trend_days_per_year',
        'LOS_Trend': 'LOS_Trend_days_per_year'
    }, inplace=True)
    
    # Reorder columns for clarity
    zonal_mean = zonal_mean[['Vegetation_Type', 'SOS_Trend_days_per_year', 'EOS_Trend_days_per_year', 'LOS_Trend_days_per_year']]
    
    print("\nZonal Statistics Results:")
    print(zonal_mean)
    
    # --- 6. Save Results to CSV ---
    zonal_mean.to_csv(output_csv, float_format='%.4f')
    print(f"\nResults saved to '{output_csv}'")

    # --- 7. Visualize Results ---
    df_plot = zonal_mean.reset_index()
    df_melted = df_plot.melt(id_vars='Vegetation_Type', 
                             value_vars=['SOS_Trend_days_per_year', 'EOS_Trend_days_per_year', 'LOS_Trend_days_per_year'],
                             var_name='Phenology_Metric', value_name='Trend (days/year)')
    
    df_melted['Phenology_Metric'] = df_melted['Phenology_Metric'].str.replace('_Trend_days_per_year', '')

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(14, 8))
    
    sns.barplot(data=df_melted, x='Vegetation_Type', y='Trend (days/year)', hue='Phenology_Metric', ax=ax)
    
    ax.set_title('Phenology Trends by Vegetation Type in Mentougou (2003-2023)', fontsize=16)
    ax.set_xlabel('Vegetation Type', fontsize=12)
    ax.set_ylabel('Trend (days/year)', fontsize=12)
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_plot, dpi=300)
    print(f"Plot saved to '{output_plot}'")

    plt.show()

if __name__ == '__main__':
    main() 