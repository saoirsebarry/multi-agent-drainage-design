#!/usr/bin/env python3
"""
Test script to verify the improved riskmapper creates meaningful flood risk maps
"""
import sys
import os
sys.path.append('.')

from riskmapper import get_ea_flood_map

def test_improved_flood_map():
    """Test the improved flood map generation"""
    
    # Test with a sample bounding box
    test_bbox = [-0.964, 51.388, -0.957, 51.392]
    test_output_dir = "workflow_output"
    
    print("Testing improved flood risk map generation...")
    print(f"BBOX: {test_bbox}")
    print(f"Output directory: {test_output_dir}")
    
    # Generate the flood map
    map_path = get_ea_flood_map(test_bbox, test_output_dir, size=(512, 512))
    
    if map_path and os.path.exists(map_path):
        file_size = os.path.getsize(map_path)
        print(f"✅ Flood map generated successfully!")
        print(f"   Path: {map_path}")
        print(f"   File size: {file_size} bytes")
        
        if file_size > 1000:  # Should be more than 1KB for a meaningful image
            print("✅ Map appears to have content (file size > 1KB)")
        else:
            print("⚠️  Map file is very small, may be empty")
    else:
        print("❌ Failed to generate flood map")

if __name__ == "__main__":
    test_improved_flood_map() 