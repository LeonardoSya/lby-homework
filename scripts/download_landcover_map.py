import ee
# import ee.mapclient # This is not needed for a non-interactive export script

# --- Authenticate and initialize GEE ---
try:
    # Explicitly provide your Google Cloud Project ID.
    # You can find this in your Google Cloud Console or GEE account settings.
    # PLEASE REPLACE 'YOUR_PROJECT_ID_HERE' WITH YOUR ACTUAL PROJECT ID.
    ee.Initialize(project='ee-leonardosya')
except Exception as e:
    print("Google Earth Engine initialization failed. Please run 'earthengine authenticate' and 'gcloud auth application-default login' in your terminal.")
    print(f"Error: {e}")
    exit()

# --- 1. Define Region of Interest (ROI) and Parameters ---
# Use the exact same ROI as in previous scripts for consistency to ensure perfect alignment.
mentougou_roi = ee.Geometry.Polygon(
    [[[115.41, 39.84],
      [115.41, 40.18],
      [116.18, 40.18],
      [116.18, 39.84],
      [115.41, 39.84]]], None, False)

# Use a representative year for land cover, e.g., the middle of the period
LULC_YEAR = '2013-01-01'

# We'll use the International Geosphere-Biosphere Programme (IGBP) classification
# which is the first band 'LC_Type1'.
LAND_COVER_BAND = 'LC_Type1'

# --- 2. Load and Process Land Cover Data ---
# Load the MODIS Land Cover Type product - using version 6.1 to avoid deprecation warning
landcover = ee.ImageCollection('MODIS/061/MCD12Q1') \
                .filterDate(LULC_YEAR) \
                .first() \
                .select(LAND_COVER_BAND)

# --- 3. Define Export Parameters to Match Phenology Rasters ---
# It's CRITICAL to match the CRS and scale of our previous analysis
# We get this information from one of the previously downloaded TIFs.
# Assuming MODIS sinusoidal projection and 500m scale.
EXPORT_CRS = 'EPSG:4326' # WGS84 a common standard for GEE exports
EXPORT_SCALE = 463.3127165275  # MODIS 500m scale in degrees, match this if known, otherwise this is a good default

# --- 4. Export the Image to Google Drive ---
task = ee.batch.Export.image.toDrive(
    image=landcover.clip(mentougou_roi).unmask(0), # unmask to avoid errors with empty areas, fill with 0
    description='landcover_export_mentougou',
    folder='GEE_Exports', # Save to the same folder as before
    fileNamePrefix='landcover_mentougou_2013',
    region=mentougou_roi,
    scale=EXPORT_SCALE,
    crs=EXPORT_CRS,
    fileFormat='GeoTIFF'
)

task.start()

print("Export task started for Land Cover map: 'landcover_mentougou_2013.tif'")
print("Please check the 'Tasks' tab in your GEE Code Editor to monitor the progress.")
print("Once completed, download the file from your 'GEE_Exports' folder in Google Drive")
print("and place it into the 'project/data/' directory.") 