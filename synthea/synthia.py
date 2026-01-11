# synthia.py (The Coordinator)
# This is the main script to run the entire workflow.

import os
import json
import time

# Import the agent modules
import geoscribe
import hydroflow
import riskmapper
import draincraft

def run_workflow():
    """
    Coordinates the multi-agent workflow from start to finish.
    """
    print("--- Starting Flood Risk Analysis Workflow ---")

    # 1. Define the Area of Interest (AOI)
    # In a real application, this would come from the web interface.
    # For this simulation, we'll use a predefined bounding box.
    aoi_poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [-0.1412, 51.5216],
                [-0.1069, 51.5216],
                [-0.1069, 51.5037],
                [-0.1412, 51.5037],
                [-0.1412, 51.5216]
            ]
        ]
    }
    print(f"Step 1: Area of Interest defined in Central London.")
    time.sleep(1)

    # Create an output directory
    output_dir = "workflow_output"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output will be saved in '{output_dir}/' directory.")

    # --- Agent Execution ---

    # 2. GeoScribe: Gather Geospatial Data
    print("\n[TASK] Activating GeoScribe (The Cartographer)...")
    my_api_key = "2163c38e1f03fb03f53b168b089328af"
    local_data_folder = "landcover_data"
    print("\n[TASK] Checking GeoScribe outputs...")
    
    # Define the expected final output files for GeoScribe
    geoscribe_dem_map = os.path.join(output_dir, "dem_map.png")
    geoscribe_lulc_map = os.path.join(output_dir, "lulc_map.png")
    
    geoscribe_outputs = {} # Initialize empty dictionary

    # Check if both final files already exist
    if os.path.exists(geoscribe_dem_map) and os.path.exists(geoscribe_lulc_map):
        print(" -> GeoScribe outputs already exist. Skipping task.")
        # If files exist, manually populate the outputs dictionary with the known paths
        geoscribe_outputs = {
            "dem_data_path": os.path.join(output_dir, "uk_dem.npy"),
            "dem_map_path": geoscribe_dem_map,
            "dem_geotiff_path": os.path.join(output_dir, "uk_dem.tif"),
            "lulc_data_path": os.path.join(output_dir, "uk_lulc.npy"),
            "lulc_map_path": geoscribe_lulc_map,
        }
    else:
        # If files don't exist, run the agent
        print(" -> Outputs not found. Activating GeoScribe...")
        geoscribe_outputs = geoscribe.run(aoi_poly, output_dir, api_key=my_api_key, local_data_folder=local_data_folder)

    print(f"GeoScribe finished. Outputs: {list(geoscribe_outputs.keys())}")

    # 3. HydroFlow: Run Hydrological Simulation
    print("\n[TASK] Activating HydroFlow (The Hydrologist)...")
    hydroflow_outputs = hydroflow.run(geoscribe_outputs, output_dir)
    
    print(f"HydroFlow finished. Outputs: {list(hydroflow_outputs.keys())}")
    time.sleep(1)

    # 4. RiskMapper: Generate Flood Risk Map
    print("\n[TASK] Activating RiskMapper (The Risk Analyst)...")
    riskmapper_outputs = riskmapper.run(geoscribe_outputs, hydroflow_outputs, output_dir)
    print(f"RiskMapper finished. Outputs: {list(riskmapper_outputs.keys())}")
    time.sleep(1)

    # 5. DrainCraft: Formulate Drainage Strategy
    print("\n[TASK] Activating DrainCraft (The Civil Engineer)...")
    draincraft_outputs = draincraft.run(riskmapper_outputs, geoscribe_outputs, output_dir)
    print(f"DrainCraft finished. Outputs: {list(draincraft_outputs.keys())}")
    time.sleep(1)

    # --- Workflow Completion ---
    print("\n--- Workflow Complete ---")
    print("Final artifacts generated:")
    all_outputs = {**geoscribe_outputs, **hydroflow_outputs, **riskmapper_outputs, **draincraft_outputs}
    for key, value in all_outputs.items():
        print(f"  - {key}: {value}")

    # Generate a final report summary
    with open(os.path.join(output_dir, "final_report.json"), "w") as f:
        json.dump(all_outputs, f, indent=4)
    print("\nFinal report summary saved to 'final_report.json'")

if __name__ == "__main__":
    run_workflow()

