#!/usr/bin/env python3
"""
Test script to debug EA WMS flood map requests
"""
import requests
from PIL import Image
from io import BytesIO
import numpy as np

def test_ea_wms():
    """Test EA WMS service with a known Flood Zone 3 area (converted from BNG to WGS84)"""
    
    # Provided BNG bbox converted to WGS84 (approximate)
    # minx, miny, maxx, maxy in WGS84
    test_bbox = [-0.964, 51.388, -0.957, 51.392]
    print(f"Testing EA WMS with bbox (WGS84): {test_bbox}")
    
    params = {
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetMap',
        'LAYERS': 'Flood_Map_for_Planning_Rivers_and_Sea_Flood_Zone_3',
        'STYLES': '',
        'CRS': 'EPSG:4326',
        'BBOX': f"{test_bbox[0]},{test_bbox[1]},{test_bbox[2]},{test_bbox[3]}",
        'WIDTH': 512,
        'HEIGHT': 512,
        'FORMAT': 'image/png',
        'TRANSPARENT': 'TRUE',
    }
    url = "https://environment.data.gov.uk/spatialdata/flood-map-for-planning-rivers-and-sea-flood-zone-3/wms"
    print(f"Requesting from: {url}")
    print(f"Parameters: {params}")
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', '')}")
        if response.status_code == 200 and 'image/' in response.headers.get('Content-Type', ''):
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            img_array = np.array(img)
            alpha = img_array[:, :, 3]
            rgb = img_array[:, :, :3]
            print(f"Alpha: min={alpha.min()}, max={alpha.max()}, mean={alpha.mean():.2f}")
            print(f"RGB: min={rgb.min()}, max={rgb.max()}, mean={rgb.mean():.2f}")
            if np.all(alpha == 0):
                print("❌ Completely transparent")
            elif np.all(rgb == 255):
                print("❌ Completely white")
            elif np.all(rgb == 0):
                print("❌ Completely black")
            else:
                print("✅ Has content!")
                img.save("test_ea_fz3_bbox.png")
                print("Saved as test_ea_fz3_bbox.png")
        else:
            print(f"HTTP Error or not an image: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ea_wms() 