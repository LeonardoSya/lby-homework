import ee
import time

def main():
    """
    This script performs a zonal statistics analysis in GEE. It calculates the
    mean annual NDVI for each land cover type within the specified region
    and exports the results to Google Drive.
    """
    try:
        ee.Initialize(project='ee-leonardosya') # Assumes project ID is set
        print("Google Earth Engine initialized successfully.")
    except ee.EEException as e:
        print(f"Error initializing GEE: {e}")
        return

    # 1. Define Study Area and Time Period
    mentougou_aoi = ee.Geometry.Rectangle([115.4, 39.8, 116.2, 40.2])
    start_year = 2003
    end_year = 2023
    years = ee.List.sequence(start_year, end_year)

    # 2. Load Datasets
    # NDVI Collection
    ndvi_collection = ee.ImageCollection('MODIS/061/MOD13A1').select('NDVI')
    
    # Land Cover Collection (using the IGBP classification scheme)
    # We use the land cover map from the first year of our study period as a representative mask.
    # For long-term studies with significant land cover change, one might use a different map for each year.
    landcover_collection = ee.ImageCollection('MODIS/061/MCD12Q1').select('LC_Type1')
    landcover_map = landcover_collection.filter(ee.Filter.calendarRange(start_year, start_year, 'year')).first()
    
    # IGBP Land Cover Palette for reference (optional, but good for context)
    igbp_legend = {
      1: 'Evergreen Needleleaf Forest', 2: 'Evergreen Broadleaf Forest', 3: 'Deciduous Needleleaf Forest',
      4: 'Deciduous Broadleaf Forest', 5: 'Mixed Forest', 6: 'Closed Shrublands', 7: 'Open Shrublands',
      8: 'Woody Savannas', 9: 'Savannas', 10: 'Grasslands', 11: 'Permanent Wetlands', 12: 'Croplands',
      13: 'Urban and Built-up', 14: 'Cropland/Natural Vegetation Mosaic', 15: 'Snow and Ice', 16: 'Barren or Sparsely Vegetated',
      17: 'Water'
    }
    
    print(f"Using Land Cover map from {start_year} for zoning.")

    # 3. Perform Zonal Statistics for Each Year
    def calculate_zonal_mean(year):
        # Calculate the mean annual NDVI for the given year
        annual_ndvi = ndvi_collection.filter(ee.Filter.calendarRange(year, year, 'year')).mean().multiply(0.0001)
        
        # Combine the NDVI and land cover map into a single image
        combined_image = annual_ndvi.addBands(landcover_map)
        
        # Calculate the mean NDVI for each land cover class
        zonal_stats = combined_image.reduceRegions(
            collection=mentougou_aoi,
            reducer=ee.Reducer.mean().group(groupField=1),
            scale=500,
            tileScale=4
        )
        
        # Extract the list of groups from the first (and only) feature.
        groups = zonal_stats.first().get('groups')
        
        # A function to map over the list of groups to format it into a list of Features.
        def map_group_to_feature(group):
            group_dict = ee.Dictionary(group)
            class_id = group_dict.get('group')
            mean_ndvi = group_dict.get('mean')
            return ee.Feature(None, {
                'year': ee.Number(year).toInt(),
                'veg_type_id': class_id,
                'mean_ndvi': mean_ndvi
            })

        # The 'groups' property can be null if there's no data.
        # Use ee.Algorithms.If to handle this case, returning a list of features or an empty list.
        # This list of features is the final result for this year.
        return ee.List(ee.Algorithms.If(
            groups, # Check if 'groups' is not null
            ee.List(groups).map(map_group_to_feature),
            ee.List([]) # Return an empty list if it's null
        ))

    # Map the function over all years and flatten the result into a single FeatureCollection
    # FIX: The result of mapping over years is a List of Lists. We must flatten this
    # nested list BEFORE passing it to the FeatureCollection constructor.
    list_of_features = years.map(calculate_zonal_mean).flatten()
    results_fc = ee.FeatureCollection(list_of_features)
    
    # 4. Export the Results
    task = ee.batch.Export.table.toDrive(
        collection=results_fc,
        description='export_zonal_ndvi_by_veg_type',
        folder='GEE_Exports',
        fileNamePrefix='zonal_ndvi_by_veg_type_mentougou',
        fileFormat='CSV'
    )
    
    task.start()
    
    print("\\nZonal statistics export task has been initiated.")
    print("Please monitor the task in the GEE Code Editor UI or wait for the file 'zonal_ndvi_by_veg_type_mentougou.csv' to appear in your Google Drive.")

if __name__ == '__main__':
    main() 