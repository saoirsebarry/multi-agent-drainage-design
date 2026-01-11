# hydroflow.py (The Hydrologist)
import numpy as np
from PIL import Image
import os
import rasterio
from pysheds.grid import Grid
import matplotlib.cm as cm
from pysheds.sview import Raster

# In hydroflow.py
# In hydroflow.py

def run(geoscribe_data, output_dir):
    """
    Performs a real hydrological flow accumulation analysis using the PySheds library.
    """
    print("  -> HydroFlow: Loading Digital Elevation Model...")

    try:
        dem_path = geoscribe_data["dem_geotiff_path"]
        lulc_path = geoscribe_data["lulc_data_path"]
        lulc_data = np.load(lulc_path)
    except (KeyError, FileNotFoundError) as e:
        print(f"  -> HydroFlow ERROR: Input data is missing or invalid. {e}")
        return None

    grid = Grid.from_raster(dem_path)
    dem_raster = grid.read_raster(dem_path)

    print("  -> HydroFlow: Conditioning DEM by filling sinks and resolving flats...")
    flooded_dem = grid.fill_depressions(dem_raster)
    inflated_dem = grid.resolve_flats(flooded_dem)

    print("  -> HydroFlow: Calculating flow direction...")
    # --- THIS IS THE CORRECTED LINE ---
    # Add nodata_out=0 to specify a valid NoData value for the integer grid
    flow_direction = grid.flowdir(inflated_dem, nodata_out=0)

    print("  -> HydroFlow: Calculating flow accumulation...")
    accumulation = grid.accumulation(flow_direction)
    
        # Resample LULC if necessary
    # Resample LULC if necessary
    if lulc_data.shape != dem_raster.shape:
        #... (resampling code) ...
        lulc_img = Image.fromarray(lulc_data.astype(np.uint8))
        resampled_img = lulc_img.resize(dem_raster.shape[::-1], Image.NEAREST)
        lulc_data = np.array(resampled_img)

    # Create the runoff weights as a numpy array
    runoff_weights_arr = np.full(dem_raster.shape, 0.3, dtype=np.float32)
    runoff_weights_arr[np.isin(lulc_data, [20, 21])] = 0.9
    runoff_weights_arr[lulc_data == 14] = 1.0

    # 2. Manually create a Raster object for the weights.
    #    It uses the numpy array and inherits spatial data from the original DEM.
    weights_raster = Raster(runoff_weights_arr,
                            viewfinder=dem_raster.viewfinder,
                            metadata=dem_raster.metadata)

    print("  -> HydroFlow: Calculating flow accumulation...")
    # 3. Pass the new Raster object to the accumulation function
    weighted_accumulation = grid.accumulation(flow_direction, weights=weights_raster)


    print("  -> HydroFlow: Generating visualization...")
    log_accumulation = np.log1p(weighted_accumulation)
    # Use np.nanmin and np.nanmax to handle potential NaN values safely
    min_val, max_val = np.nanmin(log_accumulation), np.nanmax(log_accumulation)
    if max_val == min_val:
        log_accumulation_viz = np.zeros_like(log_accumulation, dtype=np.uint8)
    else:
        log_accumulation_viz = ((log_accumulation - min_val) / (max_val - min_val) * 255)
        log_accumulation_viz = np.nan_to_num(log_accumulation_viz).astype(np.uint8)

    rgba_image = cm.viridis(log_accumulation_viz)
    rgb_image = (rgba_image[:, :, :3] * 255).astype(np.uint8)
    flow_img = Image.fromarray(rgb_image)

    flow_map_path = os.path.join(output_dir, "flow_map.png")
    flow_img.save(flow_map_path)
    print(f"  -> HydroFlow: Saved water accumulation map to {flow_map_path}")

    accumulation_data_path = os.path.join(output_dir, "real_accumulation.npy")
    np.save(accumulation_data_path, weighted_accumulation)

    return {
        "accumulation_data_path": accumulation_data_path,
        "flow_map_path": flow_map_path
    }