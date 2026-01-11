# geoscribe.py (UK Version - Using Local Files)
import numpy as np
from PIL import Image
import os
import requests
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
import geopandas as gpd
from shapely.geometry import box
from shapely.geometry import shape

# Define the target output shape for the maps
OUTPUT_SHAPE = (256, 256)

def get_dem(aoi_bbox, output_dir, api_key):
    """
    Fetches a Digital Elevation Model (DEM) from the OpenTopography API.
    This part remains unchanged.
    """
    print("  -> GeoScribe: Fetching Digital Elevation Model (DEM)...")
    if not api_key:
        print("  -> GeoScribe ERROR: OpenTopography API key is missing. Please add it to the script.")
        return None, None

    dem_path_raw = os.path.join(output_dir, "uk_dem.tif")
    dem_path_npy = os.path.join(output_dir, "uk_dem.npy")
    dem_map_path = os.path.join(output_dir, "dem_map.png")

    try:
        # --- NEW CODE TO ADD ---
        # Convert the incoming GeoJSON dictionary into a Shapely Polygon object
        polygon = shape(aoi_bbox)
        
        # Get the bounding box (west, south, east, north) from the polygon
        bounds = polygon.bounds
        # --- END OF NEW CODE ---

        api_url = "https://portal.opentopography.org/API/globaldem"
        
        # Now use the 'bounds' tuple to build the parameters
        params = {
            'demtype': 'SRTMGL1',
            'south': bounds[1],
            'north': bounds[3],
            'west': bounds[0],
            'east': bounds[2],
            'outputFormat': 'GTiff',
            'API_Key': api_key,
        }
        # ... (previous code) ...
        response = requests.get(api_url, params=params)
        response.raise_for_status()

        with open(dem_path_raw, 'wb') as f:
            f.write(response.content)
    
        # Continue with resampling for the visual map as before
        with rasterio.open(dem_path_raw) as src:
            dem_data = src.read(
                1,
                out_shape=(OUTPUT_SHAPE[0], OUTPUT_SHAPE[1]),
                resampling=Resampling.bilinear
            )
        dem_geotiff_path = dem_path_raw  # Keep the original GeoTIFF path
        np.save(dem_path_npy, dem_data)

        dem_min, dem_max = dem_data.min(), dem_data.max()
        if dem_max > dem_min:
            dem_normalized = (dem_data - dem_min) / (dem_max - dem_min) * 255
        else:
            dem_normalized = np.zeros(dem_data.shape)

        dem_img = Image.fromarray(dem_normalized.astype(np.uint8))
        dem_img.convert("L").save(dem_map_path)

        print(f"  -> GeoScribe: Saved real DEM to {dem_map_path}")
        
        # os.remove(dem_path_raw) # <-- REMOVE THIS LINE
        
        return dem_path_npy, dem_map_path, dem_geotiff_path

    except Exception as e:
        import traceback
        print(f"  -> GeoScribe ERROR: An error occurred processing the DEM.")
        # Print the full error traceback to understand the root cause
        traceback.print_exc() 
        return None, None, None


def get_uk_lulc_from_local(aoi_bbox, output_dir, local_data_path):
    """
    MODIFIED: Loads UK Land Cover data from your local files.
    """
    print("  -> GeoScribe: Loading local UKCEH Land Cover Map (LULC)...")
    lulc_path_npy = os.path.join(output_dir, "uk_lulc.npy")
    lulc_map_path = os.path.join(output_dir, "lulc_map.png")

    # --- NEW CODE TO ADD ---
    # Convert the incoming GeoJSON dictionary into a Shapely Polygon object
    polygon = shape(aoi_bbox)
    # Get the bounding box (west, south, east, north) from the polygon
    bounds = polygon.bounds
    # --- END OF NEW CODE ---

    # --- LOGIC TO CHOOSE GB or NI FILE ---
    # Get the center longitude of the area of interest using the new 'bounds' tuple
    center_lon = (bounds[0] + bounds[2]) / 2 
    if center_lon < -5.0: # A simple check for Northern Ireland
        lulc_filename = "ni2021lcm1km_dominant_target.tif"
    else: # Otherwise, assume Great Britain
        lulc_filename = "gb2021lcm1km_dominant_target.tif"
    
    local_file_path = os.path.join(local_data_path, lulc_filename)
    
    if not os.path.exists(local_file_path):
        print(f"  -> GeoScribe ERROR: Could not find file: {local_file_path}")
        print("  -> Please make sure the 'local_data_folder' path is correct.")
        return None, None

    print(f"  -> GeoScribe: Using file '{lulc_filename}'")

    colors = {
        1: (85, 170, 0), 2: (0, 115, 0), 3: (255, 255, 179),
        4: (179, 217, 179), 5: (140, 204, 140), 6: (217, 179, 217),
        7: (179, 140, 179), 8: (217, 179, 140), 9: (179, 179, 106),
        10: (140, 140, 70), 11: (106, 106, 106), 12: (179, 179, 179),
        13: (0, 179, 179), 14: (0, 70, 217), 15: (217, 217, 217),
        16: (255, 255, 255), 17: (217, 217, 140), 18: (179, 179, 106),
        19: (217, 140, 70), 20: (217, 70, 70), 21: (179, 140, 106)
    }

    try:
        # Create the geometry using the new 'bounds' tuple
        geom = box(*bounds)
        aoi_gdf = gpd.GeoDataFrame([1], geometry=[geom], crs="EPSG:4326")

        # The rest of the code is the same
        with rasterio.open(local_file_path) as src:
            aoi_reprojected = aoi_gdf.to_crs(src.crs)
            clipped_data, clipped_transform = mask(dataset=src, shapes=aoi_reprojected.geometry, crop=True)

        clipped_data = clipped_data[0]
        temp_tif_path = os.path.join(output_dir, "temp_clipped_uk.tif")
        with rasterio.open(
            temp_tif_path, 'w', driver='GTiff', height=clipped_data.shape[0],
            width=clipped_data.shape[1], count=1, dtype=clipped_data.dtype,
            crs=src.crs, transform=clipped_transform
        ) as dst:
            dst.write(clipped_data, 1)

        with rasterio.open(temp_tif_path) as src_clipped:
            lulc_data = src_clipped.read(
                1, out_shape=(OUTPUT_SHAPE[0], OUTPUT_SHAPE[1]),
                resampling=Resampling.nearest
            )
        np.save(lulc_path_npy, lulc_data)

        lulc_img = Image.new("RGB", (OUTPUT_SHAPE[1], OUTPUT_SHAPE[0]))
        pixels = lulc_img.load()
        for i in range(lulc_data.shape[0]):
            for j in range(lulc_data.shape[1]):
                pixels[j, i] = colors.get(lulc_data[i, j], (0, 0, 0))

        lulc_img.save(lulc_map_path)
        print(f"  -> GeoScribe: Saved local LULC to {lulc_map_path}")
        os.remove(temp_tif_path)
        return lulc_path_npy, lulc_map_path

    except Exception as e:
        print(f"  -> GeoScribe ERROR: An error occurred processing local LULC. {e}")
        return None, None


# --- ADD THIS FUNCTION TO THE END OF geoscribe.py ---

def run(aoi_poly, output_dir, api_key, local_data_folder):
    """
    Main entry point for the GeoScribe agent.
    
    This function coordinates fetching the DEM and loading the local LULC data,
    then returns all the generated file paths in a single dictionary.
    """
    # 1. Get the Digital Elevation Model (DEM)
    dem_data_path, dem_map_path, dem_geotiff_path = get_dem(
        aoi_poly, output_dir, api_key
    )
    if not dem_geotiff_path:
        print("  -> GeoScribe CRITICAL FAIL: Could not generate DEM. Aborting workflow.")
        return None

    # 2. Get the Land Use/Land Cover (LULC) map
    lulc_data_path, lulc_map_path = get_uk_lulc_from_local(
        aoi_poly, output_dir, local_data_folder
    )
    if not lulc_map_path:
        print("  -> GeoScribe CRITICAL FAIL: Could not generate LULC map. Aborting workflow.")
        return None

    # 3. Combine all outputs into a single dictionary and return it
    print("  -> GeoScribe: All tasks complete. Returning outputs.")
    return {
        "dem_data_path": dem_data_path,
        "dem_map_path": dem_map_path,
        "dem_geotiff_path": dem_geotiff_path,
        "lulc_data_path": lulc_data_path,
        "lulc_map_path": lulc_map_path,
    }