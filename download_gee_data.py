import ee
import pandas as pd
import time

def main():
    """
    Main function to initialize GEE, process datasets, and export data.
    """
    try:
        # Initialize the Earth Engine library.
        # This will prompt for authentication if you haven't done it before
        # in this environment.
        ee.Initialize(project='ee-leonardosya') # <-- IMPORTANT: REPLACE with your GEE Project ID
        print("Google Earth Engine initialized successfully.")
    except ee.EEException as e:
        print(f"Error initializing GEE: {e}")
        print("Please ensure you have authenticated and have a valid GEE project.")
        print("You can authenticate by running: earthengine authenticate")
        return

    # 1. Define Study Area and Time Period
    # Approximate bounding box for Mentougou District, Beijing
    mentougou_aoi = ee.Geometry.Rectangle([115.4, 39.8, 116.2, 40.2])
    start_date = '2003-01-01'
    end_date = '2023-12-31'
    
    # Target resolution in degrees. 0.05 degrees is approx 5km.
    # You can change this to 0.25 or 0.5 if needed.
    target_resolution_deg = 0.05
    # GEE works in meters, so we convert degrees to meters approximately
    target_resolution_m = target_resolution_deg * 111320 

    print(f"Study Area: Mentougou (Approx.)")
    print(f"Time Period: {start_date} to {end_date}")
    print(f"Target Resolution: {target_resolution_deg} degrees (~{target_resolution_m} m)")

    # 2. Define Datasets to Process
    datasets = {
        'NDVI': {
            'collection': 'MODIS/061/MOD13A1',
            'band': 'NDVI',
            'scale_factor': 0.0001
        },
        'EVI': {
            'collection': 'MODIS/061/MOD13A1',
            'band': 'EVI',
            'scale_factor': 0.0001
        },
        'LAI': {
            'collection': 'MODIS/061/MOD15A2H',
            'band': 'Lai_500m',
            'scale_factor': 0.1
        },
        'GPP': {
            'collection': 'MODIS/061/MOD17A2H',
            'band': 'Gpp',
            'scale_factor': 0.0001
        }
        # SIF data with >15 years is not available in a standard GEE collection.
        # Long-term SIF usually comes from specific research products (e.g., GOME-2)
        # and often requires separate download and processing.
    }

    # 3. Process and Export Each Dataset
    for param, config in datasets.items():
        print(f"\\nProcessing {param}...")
        # Load and filter the collection
        collection = (
            ee.ImageCollection(config['collection'])
            .filterDate(start_date, end_date)
            .select([config['band']])
        )

        # Function to calculate monthly averages
        def calculate_monthly_average(year, month):
            start = ee.Date.fromYMD(year, month, 1)
            end = start.advance(1, 'month')
            
            monthly_collection_for_period = collection.filterDate(start, end)

            # FIX: Use a server-side conditional to handle months that have no images.
            # This prevents the .mean() and .multiply() operations from failing on an
            # empty collection, which was causing the error for the GPP dataset.
            
            # The condition to check: does the collection for this month contain any images?
            condition = monthly_collection_for_period.size().gt(0)

            # Define what to do in each case. Both branches must return an ee.Image.
            def process_with_images():
                # If there are images, calculate the mean and apply the scale factor.
                return monthly_collection_for_period.mean().multiply(config['scale_factor'])
            
            def process_without_images():
                # If there are no images, create a completely masked image that still has the
                # correct band name. This allows reduceRegion to produce a 'null' value
                # for this month instead of throwing an error.
                return ee.Image.constant(0).toFloat().mask(ee.Image.constant(0)).rename(config['band'])

            # Use ee.Algorithms.If to run the conditional logic on the server.
            processed_image = ee.Image(ee.Algorithms.If(
                condition,
                process_with_images(),
                process_without_images()
            ))
            
            # Set date properties on the result, whether it's the real data or a masked image.
            return processed_image.set('year', year).set('month', month)

        # Generate a list of months to iterate over
        years = ee.List.sequence(ee.Date(start_date).get('year'), ee.Date(end_date).get('year'))
        months = ee.List.sequence(1, 12)
        
        # Map over years and months to create a monthly average collection
        monthly_collection = ee.ImageCollection.fromImages(
            years.map(lambda year: months.map(
                lambda month: calculate_monthly_average(year, month)
            )).flatten()
        )

        # Function to reduce region and extract value
        def extract_value(image):
            # Reduce the region to a single value (mean)
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=mentougou_aoi,
                scale=target_resolution_m,
                maxPixels=1e9
            )
            # Return a feature with the value and date properties
            return ee.Feature(None, {
                'year': image.get('year'),
                'month': image.get('month'),
                param: stats.get(config['band'])
            })

        # Map over the monthly collection to get a feature collection of results
        results_fc = monthly_collection.map(extract_value)

        # --- Exporting the data to Google Drive ---
        task = ee.batch.Export.table.toDrive(
            collection=results_fc,
            description=f'export_{param}_mentougou_{start_date}_{end_date}',
            folder='GEE_Exports', # This folder will be created in your Google Drive
            fileNamePrefix=f'{param}_mentougou_monthly',
            fileFormat='CSV'
        )
        
        task.start()
        print(f"Started export task for {param}. Check the 'Tasks' tab in GEE Code Editor or your Google Drive.")
        # We add a small delay to avoid overwhelming the GEE servers
        time.sleep(5)

    print("\\nAll export tasks have been initiated.")
    print("Please monitor the tasks in the GEE Code Editor UI (https://code.earthengine.google.com/tasks) or wait for the files to appear in your Google Drive inside the 'GEE_Exports' folder.")
    print("Note: As mentioned, long-term SIF data is not included as it's not a standard, readily available collection on GEE for this time span.")

if __name__ == '__main__':
    main() 