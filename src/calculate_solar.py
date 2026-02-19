#!/usr/bin/env python3
"""
Calculate solar generation potential for rooftop areas.

Data sources & methodology:
- Capacity factors: NREL 2023 Annual Technology Baseline (ATB)
  https://atb.nrel.gov/electricity/2023/commercial_pv
- Commercial PV assumptions based on 200kW flat-roof systems
- DC capacity factors range from 12.7% (Class 10, GHI<3.75) to 19.8% (Class 1, GHI>5.75)
- US mean capacity factor: 15.8% (NREL 2023)
"""

import pandas as pd

# =============================================================================
# NREL 2023 ATB CAPACITY FACTORS BY STATE
# =============================================================================
# These are DC capacity factors for commercial rooftop PV systems
# Based on Global Horizontal Irradiance (GHI) resource classes
# Source: NREL reV model using NSRDB solar resource data
# 
# Class 1 (GHI > 5.75): 19.8%  - Best solar (AZ, NV, NM)
# Class 2 (GHI 5.5-5.75): 19.1%
# Class 3 (GHI 5.25-5.5): 18.0%
# Class 4 (GHI 5.0-5.25): 17.1%
# Class 5 (GHI 4.75-5.0): 16.3%
# Class 6 (GHI 4.5-4.75): 16.1%
# Class 7 (GHI 4.25-4.5): 15.3%
# Class 8 (GHI 4.0-4.25): 14.6%
# Class 9 (GHI 3.75-4.0): 14.0%
# Class 10 (GHI < 3.75): 12.7% - Worst solar (WA, OR)

CAPACITY_FACTORS = {
    # Class 1-2: Sunny Southwest (GHI > 5.5)
    "Arizona": 0.198,
    "Nevada": 0.191,
    "New Mexico": 0.198,
    
    # Class 2-3: California varies by region (averaging)
    "California": 0.185,
    
    # Class 3-4: Texas & South
    "Texas": 0.175,
    "Florida": 0.171,
    "Louisiana": 0.168,
    "Hawaii": 0.180,
    
    # Class 4: Mountain West
    "Colorado": 0.171,
    "Utah": 0.175,
    
    # Class 4-5: Southeast
    "Georgia": 0.168,
    "North Carolina": 0.163,
    "South Carolina": 0.168,
    "Tennessee": 0.161,
    "Alabama": 0.168,
    
    # Class 5-6: Mid-Atlantic
    "Virginia": 0.161,
    "Maryland": 0.158,
    "New Jersey": 0.158,
    "Pennsylvania": 0.153,
    "Delaware": 0.158,
    
    # Class 6-7: Northeast
    "New York": 0.153,
    "Massachusetts": 0.153,
    "Connecticut": 0.153,
    "Rhode Island": 0.153,
    
    # Class 6-7: Midwest
    "Illinois": 0.153,
    "Michigan": 0.146,
    "Minnesota": 0.153,
    "Ohio": 0.146,
    "Indiana": 0.153,
    "Wisconsin": 0.146,
    
    # Class 9-10: Pacific Northwest (low GHI)
    "Washington": 0.140,
    "Oregon": 0.146,
}

# US Mean from NREL 2023 ATB
DEFAULT_CAPACITY_FACTOR = 0.158


# =============================================================================
# DEFAULT ASSUMPTIONS (NREL 2023 ATB + Industry Standards)
# =============================================================================

# Panel power density: 200 W/m² is conservative for 2024+
# - Standard panels: 180-200 W/m² (18-20% efficiency at 1000W/m² irradiance)
# - Premium panels: 200-220 W/m² (20-22% efficiency)
# - Using 200 W/m² as reasonable commercial default
DEFAULT_WATTS_PER_M2 = 200

# Usable roof fraction: What % of roof can actually have panels?
# Research shows 50-75% depending on building type:
# - Warehouses (simple flat roofs): 60-75%
# - Commercial buildings (more HVAC, skylights): 50-60%
# - NREL study (Gagnon et al., 2016) used 50% for small, 75% for large
# Using 60% as balanced estimate for mixed building stock
DEFAULT_USABLE_FRACTION = 0.60

# DC-to-AC ratio (inverter loading ratio): 1.23 per NREL 2023 ATB
# This is already baked into capacity factor calculations
DC_AC_RATIO = 1.23

# Degradation rate: 0.7%/year per NREL 2023 ATB
# This is already averaged into capacity factor over 30-year lifetime
ANNUAL_DEGRADATION = 0.007

# Average US home consumption: ~10,500 kWh/year (EIA 2022)
AVG_HOME_KWH_YEAR = 10500

# Grid CO2 intensity: 0.386 kg CO2/kWh (EPA eGRID 2022 US average)
GRID_CO2_KG_PER_KWH = 0.386


def estimate_solar_potential(
    building_area_m2, 
    state, 
    usable_fraction=DEFAULT_USABLE_FRACTION,
    watts_per_m2=DEFAULT_WATTS_PER_M2
):
    """
    Estimate annual solar generation for rooftop area.
    
    Based on NREL 2023 Annual Technology Baseline methodology.
    https://atb.nrel.gov/electricity/2023/commercial_pv
    
    Parameters:
    -----------
    building_area_m2 : float
        Total roof area in square meters
    state : str
        State name for capacity factor lookup
    usable_fraction : float
        Fraction of roof usable for panels (default 60%)
        Accounts for: HVAC equipment, skylights, edges, setbacks, structural limits
        Range: 0.50 (complex roofs) to 0.75 (simple warehouses)
    watts_per_m2 : float
        Peak DC watts per square meter of panel area (default 200W)
        Range: 180 (budget panels) to 220 (premium panels)
    
    Returns:
    --------
    dict with solar generation estimates including all input assumptions
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
    
    # CO2 offset using EPA eGRID 2022 US average
    co2_offset_tons = annual_kwh * GRID_CO2_KG_PER_KWH / 1000  # metric tons
    
    return {
        # Input assumptions (for transparency)
        'assumptions': {
            'usable_fraction': usable_fraction,
            'watts_per_m2': watts_per_m2,
            'capacity_factor': capacity_factor,
            'avg_home_kwh_year': AVG_HOME_KWH_YEAR,
            'grid_co2_kg_kwh': GRID_CO2_KG_PER_KWH,
        },
        # Calculated values
        'total_roof_m2': building_area_m2,
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
