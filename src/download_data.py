#!/usr/bin/env python3
"""
Download Microsoft Building Footprints for required states.
Data source: https://github.com/microsoft/USBuildingFootprints
"""

import requests
import os
from tqdm import tqdm

# States needed for the 30 airports
STATES_NEEDED = [
    "Georgia", "Texas", "Colorado", "Illinois", "California", 
    "NewYork", "Nevada", "Florida", "NorthCarolina", "Washington",
    "Arizona", "Massachusetts", "NewJersey", "Minnesota", "Michigan",
    "Pennsylvania", "Maryland", "Virginia", "Tennessee", "Hawaii"
]

# Mapping from our state names to Microsoft's URL format
STATE_URL_MAP = {
    "Georgia": "Georgia",
    "Texas": "Texas",
    "Colorado": "Colorado",
    "Illinois": "Illinois",
    "California": "California",
    "NewYork": "NewYork",
    "Nevada": "Nevada",
    "Florida": "Florida",
    "NorthCarolina": "NorthCarolina",
    "Washington": "Washington",
    "Arizona": "Arizona",
    "Massachusetts": "Massachusetts",
    "NewJersey": "NewJersey",
    "Minnesota": "Minnesota",
    "Michigan": "Michigan",
    "Pennsylvania": "Pennsylvania",
    "Maryland": "Maryland",
    "Virginia": "Virginia",
    "Tennessee": "Tennessee",
    "Hawaii": "Hawaii",
}

def download_building_footprints(state, output_dir="data/buildings"):
    """Download Microsoft building footprints for a state."""
    os.makedirs(output_dir, exist_ok=True)
    
    state_url = STATE_URL_MAP.get(state, state)
    url = f"https://usbuildingdata.blob.core.windows.net/usbuildings-v2/{state_url}.geojson.zip"
    
    output_path = os.path.join(output_dir, f"{state}.geojson.zip")
    
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✓ Already have {state} ({size_mb:.1f} MB)")
        return output_path
    
    print(f"Downloading {state}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=state) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✓ Downloaded {state} ({size_mb:.1f} MB)")
        return output_path
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download {state}: {e}")
        return None

def download_all():
    """Download building footprints for all required states."""
    print("=" * 60)
    print("DOWNLOADING MICROSOFT BUILDING FOOTPRINTS")
    print("=" * 60)
    print(f"States to download: {len(STATES_NEEDED)}")
    print("Note: Total download size is approximately 5-8 GB")
    print("=" * 60)
    
    successful = 0
    failed = []
    
    for state in STATES_NEEDED:
        result = download_building_footprints(state)
        if result:
            successful += 1
        else:
            failed.append(state)
    
    print("\n" + "=" * 60)
    print(f"Download complete: {successful}/{len(STATES_NEEDED)} states")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print("=" * 60)

if __name__ == "__main__":
    download_all()
