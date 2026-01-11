# draincraft.py (The Civil Engineer)
import numpy as np
from PIL import Image, ImageDraw, ImageFont # Import ImageDraw and ImageFont
import os

def run(riskmapper_outputs, geoscribe_outputs, output_dir):
    """
    Identifies high-risk urban zones and proposes drainage solutions.
    """
    print("  -> DrainCraft: Analyzing high-risk zones...")
    
    try:
        risk_data_path = riskmapper_outputs["risk_data_path"]
        risk_map_path = riskmapper_outputs["risk_map_path"]
        lulc_data_path = geoscribe_outputs["lulc_data_path"]
        risk_data = np.load(risk_data_path)
        lulc_data = np.load(lulc_data_path)
    except (KeyError, FileNotFoundError) as e:
        print(f"  -> DrainCraft ERROR: Input data is missing or invalid. {e}")
        return None

    # Resize LULC data to match the risk map grid
    if lulc_data.shape != risk_data.shape:
        print("  -> DrainCraft: Resizing LULC data to match risk map grid...")
        lulc_img = Image.fromarray(lulc_data)
        resized_img = lulc_img.resize(risk_data.shape[::-1], Image.NEAREST)
        lulc_data = np.array(resized_img)

    # Find where High Risk (value 3) intersects with Urban (values 20 or 21)
    is_high_risk = (risk_data == 3)
    is_urban = np.isin(lulc_data, [20, 21])
    
    high_risk_urban_zones = np.argwhere(is_high_risk & is_urban)
    
    if high_risk_urban_zones.size == 0:
        print("  -> DrainCraft: No high-risk urban zones found. No action needed.")
        # Copy the original risk map as the output for this step
        import shutil
        solutions_map_path = os.path.join(output_dir, "solutions_map.png")
        shutil.copy(risk_map_path, solutions_map_path)
        return {"solutions_map_path": solutions_map_path}

    print(f"  -> DrainCraft: Found {len(high_risk_urban_zones)} high-risk urban locations. Proposing solutions...")

    # --- THIS IS THE CORRECTED SECTION ---
    # 1. Open the existing risk map to draw on it
    solutions_img = Image.open(risk_map_path).convert("RGB")
    
    # 2. Create the 'draw' object
    draw = ImageDraw.Draw(solutions_img)

    # Propose solutions by drawing on the map
    for coord in high_risk_urban_zones:
        # coord is [row, col], but PIL uses [x, y] which is [col, row]
        y, x = coord[0], coord[1]
        # Draw a blue circle to represent a proposed soakaway or drainage system
        draw.ellipse([(x-5, y-5), (x+5, y+5)], outline="blue", width=3)

    # Add a legend to the image
    try:
        font = ImageFont.truetype("Arial.ttf", size=12)
    except IOError:
        font = ImageFont.load_default() # Fallback font
    
    draw.rectangle([(5, 5), (20, 20)], fill="blue", outline="white")
    draw.text((25, 8), "Proposed Drainage Solution", fill="white", font=font)

    solutions_map_path = os.path.join(output_dir, "solutions_map.png")
    solutions_img.save(solutions_map_path)
    print(f"  -> DrainCraft: Saved proposed solutions map to {solutions_map_path}")

    return {
        "solutions_map_path": solutions_map_path
    }