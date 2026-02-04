#!/usr/bin/env python3
"""
Airport Rooftop Solar Potential Analysis
Main script to run the complete analysis pipeline.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.download_data import download_building_footprints, STATES_NEEDED
from src.extract_airport_buildings import load_airports, process_all_airports
from src.calculate_solar import calculate_all_airports, print_summary
from src.visualize import create_overview_map, create_airport_detail_map


def main():
    print("=" * 70)
    print("   AIRPORT ROOFTOP SOLAR POTENTIAL ANALYSIS")
    print("   Analyzing warehouse/logistics rooftops near 30 major US airports")
    print("=" * 70)
    
    # Create output directories
    os.makedirs("output/results", exist_ok=True)
    os.makedirs("output/maps", exist_ok=True)
    
    # Step 1: Download building data
    print("\n[1/4] DOWNLOADING BUILDING DATA")
    print("-" * 50)
    print("Note: This downloads ~5-8 GB of data. Skip if already downloaded.")
    print("      Press Ctrl+C to skip if data already exists.")
    
    try:
        for state in STATES_NEEDED:
            download_building_footprints(state)
    except KeyboardInterrupt:
        print("\nDownload skipped.")
    
    # Step 2: Load airports and extract buildings
    print("\n[2/4] EXTRACTING BUILDINGS NEAR AIRPORTS")
    print("-" * 50)
    
    airports = load_airports()
    print(f"Loaded {len(airports)} airports")
    
    # You can limit to fewer airports for testing:
    # airports = airports[:5]  # Just first 5
    
    airport_results = process_all_airports(airports, radius_km=8)
    
    # Step 3: Calculate solar potential
    print("\n[3/4] CALCULATING SOLAR POTENTIAL")
    print("-" * 50)
    
    solar_df = calculate_all_airports(airport_results)
    
    # Save results
    csv_path = "output/results/airport_solar_summary.csv"
    solar_df.to_csv(csv_path, index=False)
    print(f"✓ Results saved to {csv_path}")
    
    # Step 4: Generate visualizations
    print("\n[4/4] GENERATING VISUALIZATIONS")
    print("-" * 50)
    
    # Overview map
    create_overview_map(airport_results, solar_df, "output/maps/airport_solar_overview.html")
    
    # Optional: Generate detail maps for top airports
    print("\nGenerating detail maps for top 5 airports...")
    top5 = solar_df.head(5)
    solar_dict = solar_df.set_index('airport_code').to_dict('index')
    
    for result in airport_results:
        if result['airport_code'] in top5['airport_code'].values:
            stats = solar_dict[result['airport_code']]
            create_airport_detail_map(
                result, 
                result.get('buildings_gdf'),
                stats
            )
    
    # Print summary
    print_summary(solar_df)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nOutput files:")
    print(f"  - Results CSV:  output/results/airport_solar_summary.csv")
    print(f"  - Overview map: output/maps/airport_solar_overview.html")
    print(f"  - Detail maps:  output/maps/[AIRPORT]_detail.html")
    print("\nOpen the HTML files in a browser to explore the interactive maps!")


def quick_test():
    """Run a quick test with just one airport."""
    print("Running quick test with Atlanta (ATL)...")
    
    from src.extract_airport_buildings import (
        load_airports, load_state_buildings, extract_buildings_near_airport
    )
    from src.calculate_solar import estimate_solar_potential
    
    airports = load_airports()
    atl = [a for a in airports if a['code'] == 'ATL'][0]
    
    print(f"\nAirport: {atl['name']}")
    print(f"Location: {atl['lat']}, {atl['lon']}")
    
    buildings = load_state_buildings("Georgia")
    if buildings is None:
        print("\n⚠️  Building data not found!")
        print("Run: python src/download_data.py")
        print("Or download Georgia.geojson.zip manually from:")
        print("https://usbuildingdata.blob.core.windows.net/usbuildings-v2/Georgia.geojson.zip")
        return
    
    nearby = extract_buildings_near_airport(atl, buildings, radius_km=8)
    total_area = nearby['area_m2'].sum()
    
    print(f"\nBuildings found: {len(nearby):,}")
    print(f"Total roof area: {total_area:,.0f} m² ({total_area * 10.764:,.0f} sq ft)")
    
    solar = estimate_solar_potential(total_area, "Georgia")
    
    print(f"\nSolar Potential:")
    print(f"  Usable area: {solar['usable_area_sqft']:,.0f} sq ft")
    print(f"  Peak capacity: {solar['peak_capacity_mw']:.1f} MW")
    print(f"  Annual generation: {solar['annual_gwh']:.1f} GWh")
    print(f"  Equivalent homes: {solar['equivalent_homes']:,.0f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Airport Rooftop Solar Analysis")
    parser.add_argument('--test', action='store_true', help='Run quick test with one airport')
    parser.add_argument('--download-only', action='store_true', help='Only download data')
    
    args = parser.parse_args()
    
    if args.test:
        quick_test()
    elif args.download_only:
        for state in STATES_NEEDED:
            download_building_footprints(state)
    else:
        main()
