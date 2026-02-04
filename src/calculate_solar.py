#!/usr/bin/env python3
"""
Calculate solar generation potential for rooftop areas.
"""

import pandas as pd

# Solar capacity factors by state (from NREL data)
# This represents the fraction of peak capacity achieved on average
# Accounts for: sun angle, weather, daylight hours
CAPACITY_FACTORS = {
    # Sunny Southwest
    "Arizona": 0.26,
    "Nevada": 0.25,
    "California": 0.24,
    "New Mexico": 0.25,
    
    # Texas & South
    "Texas": 0.22,
    "Florida": 0.21,
    "Louisiana": 0.20,
    
    # Mountain West
    "Colorado": 0.22,
    "Utah": 0.23,
    
    # Southeast
    "Georgia": 0.19,
    "North Carolina": 0.18,
    "South Carolina": 0.19,
    "Tennessee": 0.18,
    "Alabama": 0.19,
    
    # Mid-Atlantic
    "Virginia": 0.17,
    "Maryland": 0.17,
    "New Jersey": 0.17,
    "Pennsylvania": 0.16,
    "Delaware": 0.17,
    
    # Northeast
    "New York": 0.16,
    "Massachusetts": 0.16,
    "Connecticut": 0.16,
    "Rhode Island": 0.16,
    
    # Midwest
    "Illinois": 0.16,
    "Michigan": 0.15,
    "Minnesota": 0.16,
    "Ohio": 0.15,
    "Indiana": 0.16,
    "Wisconsin": 0.15,
    
    # Pacific Northwest
    "Washington": 0.15,
    "Oregon": 0.16,
    
    # Islands
    "Hawaii": 0.22,
}

# Default for unlisted states
DEFAULT_CAPACITY_FACTOR = 0.17


def estimate_solar_potential(
    building_area_m2, 
    state, 
    usable_fraction=0.60,
    watts_per_m2=200
):
    """
    Estimate annual solar generation for rooftop area.
    
    Parameters:
    -----------
    building_area_m2 : float
        Total roof area in square meters
    state : str
        State name for capacity factor lookup
    usable_fraction : float
        Fraction of roof usable for panels (default 60%)
        Accounts for: HVAC equipment, skylights, edges, structural issues
    watts_per_m2 : float
        Peak watts per square meter of panel (default 200W)
        Modern commercial panels achieve 200-220 W/m²
    
    Returns:
    --------
    dict with solar generation estimates
    """
    # Get capacity factor for state
    capacity_factor = CAPACITY_FACTORS.get(state, DEFAULT_CAPACITY_FACTOR)
    
    # Calculate usable area
    usable_area_m2 = building_area_m2 * usable_fraction
    usable_area_sqft = usable_area_m2 * 10.764
    
    # Peak capacity (DC)
    peak_kw = usable_area_m2 * watts_per_m2 / 1000
    peak_mw = peak_kw / 1000
    
    # Annual generation
    # Formula: Peak Power × Hours/Year × Capacity Factor
    hours_per_year = 8760
    annual_kwh = peak_kw * hours_per_year * capacity_factor
    annual_mwh = annual_kwh / 1000
    annual_gwh = annual_mwh / 1000
    
    # Context metrics
    # Average US home uses ~10,500 kWh/year
    equivalent_homes = annual_kwh / 10500
    
    # CO2 offset (US grid average: ~0.4 kg CO2 per kWh)
    co2_offset_tons = annual_kwh * 0.0004  # metric tons
    
    return {
        'usable_area_m2': usable_area_m2,
        'usable_area_sqft': usable_area_sqft,
        'peak_capacity_kw': peak_kw,
        'peak_capacity_mw': peak_mw,
        'capacity_factor': capacity_factor,
        'annual_kwh': annual_kwh,
        'annual_mwh': annual_mwh,
        'annual_gwh': annual_gwh,
        'equivalent_homes': equivalent_homes,
        'co2_offset_tons': co2_offset_tons,
    }


def calculate_all_airports(airport_results):
    """
    Calculate solar potential for all airports.
    
    Parameters:
    -----------
    airport_results : list
        List of dicts from extract_airport_buildings.process_all_airports()
    
    Returns:
    --------
    pandas DataFrame with solar calculations for each airport
    """
    summary = []
    
    for result in airport_results:
        solar = estimate_solar_potential(
            result['total_building_area_m2'],
            result['state']
        )
        
        summary.append({
            # Airport info
            'airport_code': result['airport_code'],
            'airport_name': result['airport_name'],
            'state': result['state'],
            'lat': result['lat'],
            'lon': result['lon'],
            
            # Building stats
            'num_buildings': result['num_buildings'],
            'total_roof_area_m2': result['total_building_area_m2'],
            'total_roof_area_sqft': result['total_building_area_m2'] * 10.764,
            
            # Solar potential
            'usable_area_m2': solar['usable_area_m2'],
            'usable_area_sqft': solar['usable_area_sqft'],
            'peak_capacity_kw': solar['peak_capacity_kw'],
            'peak_capacity_mw': solar['peak_capacity_mw'],
            'capacity_factor': solar['capacity_factor'],
            'annual_kwh': solar['annual_kwh'],
            'annual_mwh': solar['annual_mwh'],
            'annual_gwh': solar['annual_gwh'],
            'equivalent_homes': solar['equivalent_homes'],
            'co2_offset_tons': solar['co2_offset_tons'],
        })
    
    df = pd.DataFrame(summary)
    
    # Sort by potential (descending)
    df = df.sort_values('annual_gwh', ascending=False)
    
    return df


def print_summary(df):
    """Print a summary of the analysis results."""
    print("\n" + "=" * 70)
    print("AIRPORT ROOFTOP SOLAR POTENTIAL - SUMMARY")
    print("=" * 70)
    
    print(f"\nAirports analyzed: {len(df)}")
    print(f"Total buildings found: {df['num_buildings'].sum():,}")
    print(f"Total roof area: {df['total_roof_area_m2'].sum():,.0f} m² ({df['total_roof_area_sqft'].sum():,.0f} sq ft)")
    
    print(f"\n--- SOLAR POTENTIAL ---")
    print(f"Total usable roof area: {df['usable_area_m2'].sum():,.0f} m²")
    print(f"Total peak capacity: {df['peak_capacity_mw'].sum():,.0f} MW")
    print(f"Total annual generation: {df['annual_gwh'].sum():,.1f} GWh")
    print(f"Equivalent homes powered: {df['equivalent_homes'].sum():,.0f}")
    print(f"Annual CO2 offset: {df['co2_offset_tons'].sum():,.0f} metric tons")
    
    print(f"\n--- TOP 10 AIRPORTS BY SOLAR POTENTIAL ---")
    top10 = df.head(10)[['airport_code', 'airport_name', 'num_buildings', 
                          'peak_capacity_mw', 'annual_gwh', 'equivalent_homes']]
    top10.columns = ['Code', 'Airport', 'Buildings', 'Peak MW', 'Annual GWh', 'Homes Equiv']
    print(top10.to_string(index=False))
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Test with sample data
    test_results = [
        {
            'airport_code': 'ATL',
            'airport_name': 'Atlanta',
            'state': 'Georgia',
            'lat': 33.64,
            'lon': -84.43,
            'num_buildings': 5000,
            'total_building_area_m2': 8000000,
        },
        {
            'airport_code': 'PHX',
            'airport_name': 'Phoenix',
            'state': 'Arizona',
            'lat': 33.44,
            'lon': -112.01,
            'num_buildings': 3000,
            'total_building_area_m2': 5000000,
        },
    ]
    
    df = calculate_all_airports(test_results)
    print_summary(df)
