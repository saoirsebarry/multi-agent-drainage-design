# main.py
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any
from dotenv import load_dotenv
from shapely.geometry import shape 


# Import your agent modules
import geoscribe
import hydroflow
import riskmapper
import draincraft
# import storyweaver # Optional: if you want the final HTML report

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# Create a .env file in your project folder and add your API key:
# OPENTOPOGRAPHY_API_KEY="YOUR_ACTUAL_KEY_HERE"
API_KEY = os.getenv("OPENTOPOGRAPHY_API_KEY")
OUTPUT_DIR = "workflow_output"
LANDCOVER_DATA_DIR = "landcover_data"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define the data structure for the incoming request
class AOIRequest(BaseModel):
    aoi: Dict[str, Any]

# Initialize the FastAPI app
app = FastAPI()

@app.post("/run-workflow")
async def run_full_workflow(request: AOIRequest):
    """
    This endpoint receives the AOI from the frontend, runs the entire
    multi-agent workflow, and returns the paths to the generated maps.
    """
    aoi_poly = request.aoi
    aoi_shape = shape(aoi_poly)
    aoi_bbox = aoi_shape.bounds # This creates the (west, south, east, north) tuple
    

    # --- Run the agent workflow ---
    print("\n[TASK] Activating GeoScribe...")
    geoscribe_outputs = geoscribe.run(aoi_poly, OUTPUT_DIR, api_key=API_KEY, local_data_folder=LANDCOVER_DATA_DIR)
    if not geoscribe_outputs or not geoscribe_outputs.get("dem_geotiff_path"):
        return {"error": "GeoScribe failed to produce the required DEM file."}

    print("\n[TASK] Activating HydroFlow...")
    # FIX: The hydroflow agent does not require the aoi_bbox argument.
    hydroflow_outputs = hydroflow.run(geoscribe_outputs, OUTPUT_DIR)
    if not hydroflow_outputs:
        return {"error": "HydroFlow failed to produce outputs."}

    print("\n[TASK] Activating RiskMapper...")
    # FIX: The aoi_bbox argument must be passed as a keyword argument.
    riskmapper_outputs = riskmapper.run(
        geoscribe_outputs, 
        hydroflow_outputs, 
        aoi_bbox=aoi_bbox
    )
    if not riskmapper_outputs:
        return {"error": "RiskMapper failed to produce outputs."}

    print("\n[TASK] Activating DrainCraft...")
    draincraft_outputs = draincraft.run(riskmapper_outputs, geoscribe_outputs, OUTPUT_DIR)
    if not draincraft_outputs:
        return {"error": "DrainCraft failed to produce outputs."}

    # --- Consolidate and return all output paths ---
    all_outputs = {
        **geoscribe_outputs,
        **hydroflow_outputs,
        **riskmapper_outputs,
        **draincraft_outputs,
    }
    
    # Prepend a "/" to make paths absolute for the web server
    final_paths = {key: "/" + value for key, value in all_outputs.items() if value}

    return final_paths

# Serve the main index.html file
@app.get("/")
async def read_index():
    return FileResponse('index.html')

# Serve static files (like images from workflow_output)
# This mounts the 'workflow_output' directory to be accessible at '/workflow_output'
app.mount("/workflow_output", StaticFiles(directory=OUTPUT_DIR), name="workflow_output")
