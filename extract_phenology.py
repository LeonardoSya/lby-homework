import ee
import time

def main():
    """
    This script performs per-pixel phenology extraction (SOS, EOS, Peak)
    using a harmonic model to smooth the NDVI time series, followed by a
    dynamic threshold method.
    """
    try:
        ee.Initialize(project='ee-leonardosya') # Assumes project ID is set
        print("Google Earth Engine initialized successfully.")
    except ee.EEException as e:
        print(f"Error initializing GEE: {e}")
        return

    # --- 1. Configuration ---
    study_area = ee.Geometry.Rectangle([115.4, 39.8, 116.2, 40.2])
    start_year = 2003
    end_year = 2023 # Using a smaller range for quick testing is advised
    years = ee.List.sequence(start_year, end_year)
    
    # Phenology parameters
    amplitude_threshold = 0.5 # 50% of the amplitude
    
    # Harmonic model parameters
    harmonics = 3 # Number of harmonic pairs (sin, cos)

    # --- 2. Helper Functions ---
    def add_time_bands(image):
        """Adds bands for time in fractional years to use in harmonic regression."""
        date = image.date()
        years_since_epoch = date.difference(ee.Date('1970-01-01'), 'year')
        time_radians = years_since_epoch.multiply(2 * np.pi)
        return image.addBands(time_radians.rename('t').float())

    def add_harmonic_bands(image):
        """Adds harmonic bands (sin and cos) to the image."""
        time_radians = image.select('t')
        for i in range(1, harmonics + 1):
            sin = time_radians.multiply(i).sin().rename(f'sin_{i}')
            cos = time_radians.multiply(i).cos().rename(f'cos_{i}')
            image = image.addBands(sin).addBands(cos)
        return image

    # --- 3. Main Phenology Extraction Function (for a single year) ---
    def extract_phenology_for_year(year):
        year = ee.Number(year)
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = ee.Date.fromYMD(year, 12, 31)

        # Load, filter, and preprocess NDVI data for the year
        ndvi_collection = (
            ee.ImageCollection('MODIS/061/MOD13A1')
            .select('NDVI')
            .filterDate(start_date, end_date)
            .map(lambda img: img.multiply(0.0001))
            .map(add_time_bands)
            .map(add_harmonic_bands)
        )

        # Define harmonic band names for the regression
        harmonic_bands = ['constant']
        for i in range(1, harmonics + 1):
            harmonic_bands.extend([f'cos_{i}', f'sin_{i}'])

        # Fit the harmonic model
        harmonic_fit = ndvi_collection \
            .select(harmonic_bands + ['NDVI']) \
            .reduce(ee.Reducer.linearRegression(numX=len(harmonic_bands), numY=1))

        # --- Create a daily time series to apply the model ---
        days_of_year = ee.List.sequence(1, 365)
        def create_daily_image(day):
            date = start_date.advance(ee.Number(day).subtract(1), 'day')
            time_radians = ee.Date(date).difference(ee.Date('1970-01-01'), 'year').multiply(2 * np.pi)
            
            image = ee.Image(1).addBands(time_radians.rename('t').float())
            image = add_harmonic_bands(image).select(harmonic_bands)
            
            # Predict NDVI using the fitted model
            predicted_ndvi = image.multiply(harmonic_fit.select('coefficients')) \
                                .reduce('sum') \
                                .rename('NDVI')
            return predicted_ndvi.addBands(ee.Image(day).rename('doy').int16())

        daily_smoothed_collection = ee.ImageCollection.fromImages(days_of_year.map(create_daily_image))

        # --- Extract Phenology Metrics from the smoothed curve ---
        
        # Get min, max, and peak day of year (doy)
        quality_band = daily_smoothed_collection.qualityMosaic('NDVI')
        peak_doy = quality_band.select('doy').rename('peak')
        max_ndvi = quality_band.select('NDVI')
        min_ndvi = daily_smoothed_collection.select('NDVI').min()
        
        # Calculate amplitude and threshold
        amplitude = max_ndvi.subtract(min_ndvi)
        threshold = min_ndvi.add(amplitude.multiply(amplitude_threshold))

        # Find SOS and EOS
        greenup_phase = daily_smoothed_collection.map(lambda img: img.select('NDVI').gt(threshold))
        
        # SOS: first day when smoothed NDVI > threshold
        sos_image = greenup_phase.select('NDVI').where(greenup_phase.select('NDVI').eq(0), 1000)
        sos_doy = sos_image.multiply(daily_smoothed_collection.select('doy')).min().rename('sos')
        
        # EOS: last day when smoothed NDVI > threshold
        senescence_phase = daily_smoothed_collection.map(lambda img: img.select('NDVI').lt(threshold))
        eos_image = senescence_phase.select('NDVI').where(senescence_phase.select('NDVI').eq(0), 1000)
        eos_doy = eos_image.multiply(daily_smoothed_collection.select('doy')).min().subtract(1).rename('eos')

        return sos_doy.addBands(eos_doy).addBands(peak_doy).set('year', year)


    # --- 4. Loop and Export ---
    print("Starting phenology extraction and export process...")
    for i in range(start_year, end_year + 1):
        year = i
        print(f"Processing year: {year}...")
        
        phenology_image = extract_phenology_for_year(year)
        
        task = ee.batch.Export.image.toDrive(
            image=phenology_image.toFloat(),
            description=f'phenology_export_{year}',
            folder='GEE_Phenology_Exports',
            fileNamePrefix=f'phenology_mentougou_{year}',
            region=study_area,
            scale=500,
            maxPixels=1e10
        )
        task.start()
        print(f"  - Task started for year {year}.")
        time.sleep(5) # Small delay to avoid overwhelming the server with requests

    print("\\nAll phenology export tasks have been initiated.")
    print("Please monitor the tasks in the GEE Code Editor UI. This may take a significant amount of time.")


if __name__ == '__main__':
    # Add a temporary numpy import for the script to run locally
    import numpy as np
    main() 