#!/usr/bin/env python3
"""
Extract buildings near airports from Microsoft Building Footprints.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely.ops import transform
import pyproj
import os

def load_airports(csv_path="data/airports/top_30_airports.csv"):
    """Load airport data from CSV."""
    df = pd.read_csv(csv_path)
    return df.to_dict('records')

def create_buffer_km(lat, lon, radius_km):
    """Create a circular buffer around a point in kilometers."""
    # WGS84 to Web Mercator for meter-based buffering
    project_to_meters = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:3857", always_xy=True
    ).transform
    project_to_latlon = pyproj.Transformer.from_crs(
        "EPSG:3857", "EPSG:4326", always_xy=True
    ).transform
    
    point = Point(lon, lat)
    point_m = transform(project_to_meters, point)
    buffer_m = point_m.buffer(radius_km * 1000)
    buffer_latlon = transform(project_to_latlon, buffer_m)
    return buffer_latlon

def load_state_buildings(state, buildings_dir="data/buildings"):
    """Load building footprints for a state."""
    # Handle state name variations
    state_clean = state.replace(" ", "")
    path = os.path.join(buildings_dir, f"{state_clean}.geojson.zip")
    
    if not os.path.exists(path):
        print(f"  Warning: Building data not found for {state}")
        return None
    
    print(f"  Loading buildings for {state}...")
    return gpd.read_file(f"zip://{path}")

def extract_buildings_near_airport(airport, buildings_gdf, radius_km=8):
    """Extract buildings within radius of airport."""
    if buildings_gdf is None:
        return gpd.GeoDataFrame()
    
    buffer = create_buffer_km(airport['lat'], airport['lon'], radius_km)
    buffer_gdf = gpd.GeoDataFrame(geometry=[buffer], crs="EPSG:4326")
    
    # Ensure buildings have same CRS
    if buildings_gdf.crs != "EPSG:4326":
        buildings_gdf = buildings_gdf.to_crs("EPSG:4326")
    
    # Spatial join to find buildings within buffer
    buildings_in_area = gpd.sjoin(buildings_gdf, buffer_gdf, predicate='within')
    
    if len(buildings_in_area) == 0:
        return gpd.GeoDataFrame()
    
    # Calculate building areas (project to equal-area CRS)
    buildings_projected = buildings_in_area.to_crs("EPSG:3857")
    buildings_in_area = buildings_in_area.copy()
    buildings_in_area['area_m2'] = buildings_projected.geometry.area
    
    # Filter for large commercial buildings (>500 sq meters = ~5,400 sq ft)
    # This filters out houses and small buildings
    large_buildings = buildings_in_area[buildings_in_area['area_m2'] > 500].copy()
    
    return large_buildings

def process_all_airports(airports=None, radius_km=8):
    """Process all airports and extract nearby buildings."""
    if airports is None:
        airports = load_airports()
    
    results = []
    
    # Group airports by state to minimize file loading
    airports_by_state = {}
    for airport in airports:
        state = airport['state'].replace(" ", "")
        if state not in airports_by_state:
            airports_by_state[state] = []
        airports_by_state[state].append(airport)
    
    for state, state_airports in airports_by_state.items():
        buildings = load_state_buildings(state)
        
        for airport in state_airports:
            print(f"  Processing {airport['code']} ({airport['name']})...")
            nearby_buildings = extract_buildings_near_airport(airport, buildings, radius_km)
            
            if len(nearby_buildings) > 0:
                total_area = nearby_buildings['area_m2'].sum()
            else:
                total_area = 0
            
            results.append({
                'airport_code': airport['code'],
                'airport_name': airport['name'],
                'state': airport['state'],
                'lat': airport['lat'],
                'lon': airport['lon'],
                'num_buildings': len(nearby_buildings),
                'total_building_area_m2': total_area,
                'buildings_gdf': nearby_buildings
            })
            
            print(f"    Found {len(nearby_buildings):,} large buildings, {total_area:,.0f} m² total")
    
    return results

if __name__ == "__main__":
    print("Testing with one airport...")
    airports = load_airports()
    
    # Test with just Atlanta
    test_airport = [a for a in airports if a['code'] == 'ATL'][0]
    buildings = load_state_buildings("Georgia")
    
    if buildings is not None:
        nearby = extract_buildings_near_airport(test_airport, buildings, radius_km=8)
        print(f"Found {len(nearby)} large buildings near ATL")
        print(f"Total area: {nearby['area_m2'].sum():,.0f} m²")
