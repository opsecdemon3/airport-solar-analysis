"""
Single source of truth for all solar-related constants and parameters.

Data sources & methodology:
- Capacity factors: NREL 2023 Annual Technology Baseline (ATB)
  https://atb.nrel.gov/electricity/2023/commercial_pv
- Commercial PV assumptions based on 200kW flat-roof systems
- DC capacity factors range from 12.7% (Class 10) to 19.8% (Class 1)
- Install costs: SEIA/Wood Mackenzie U.S. Solar Market Insight 2025
- Grid emissions: EPA eGRID 2022
"""

# =============================================================================
# NREL 2023 ATB CAPACITY FACTORS BY STATE
# =============================================================================
# AC capacity factors for commercial rooftop PV
# Based on Global Horizontal Irradiance (GHI) resource classes
# ~14% system losses included: inverter 96%, soiling 2%, wiring 2%,
# mismatch 2%, availability 3%, age 1.5%

CAPACITY_FACTORS = {
    # Class 1-2: Sunny Southwest (GHI > 5.5)
    "Arizona": 0.198,
    "Nevada": 0.191,
    "New Mexico": 0.198,

    # Class 2-3: California varies by region
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

    # Class 9-10: Pacific Northwest
    "Washington": 0.140,
    "Oregon": 0.146,
}

# US mean from NREL 2023 ATB
DEFAULT_CAPACITY_FACTOR = 0.158

# =============================================================================
# PANEL & INSTALLATION DEFAULTS
# =============================================================================

# Panel power density: 200 W/m² (standard 20% efficiency commercial panels)
DEFAULT_WATTS_PER_M2 = 200

# Usable roof fraction: 60% (NREL Gagnon et al., 2016)
DEFAULT_USABLE_FRACTION = 0.60

# Installation cost per watt (commercial rooftop, 2025 — SEIA/Wood Mackenzie)
INSTALL_COST_PER_WATT = 1.40

# =============================================================================
# FINANCIAL DEFAULTS
# =============================================================================

# Federal Investment Tax Credit (ITC) — 30% for commercial solar through 2032
ITC_RATE = 0.30

# Annual panel degradation rate (NREL 2023 ATB)
ANNUAL_DEGRADATION = 0.005  # 0.5%/year

# System lifetime in years
SYSTEM_LIFETIME_YEARS = 25

# Discount rate for NPV calculations
DEFAULT_DISCOUNT_RATE = 0.06  # 6%

# O&M cost per kW/year (NREL 2023 ATB)
OM_COST_PER_KW_YEAR = 15.0

# =============================================================================
# ENVIRONMENTAL CONSTANTS
# =============================================================================

# Grid CO2 intensity by EPA eGRID subregion (kg CO2/kWh, 2022)
GRID_CO2_KG_PER_KWH = 0.386

# Average US home consumption (EIA 2022)
AVG_HOME_KWH_YEAR = 10_500

# Hours per year
HOURS_PER_YEAR = 8_760

# =============================================================================
# EPA eGRID SUBREGION CO2 RATES BY STATE (kg CO2/kWh, 2022)
# =============================================================================

STATE_CO2_RATES = {
    "Arizona": 0.397,
    "California": 0.211,
    "Colorado": 0.525,
    "Florida": 0.379,
    "Georgia": 0.404,
    "Hawaii": 0.531,
    "Illinois": 0.301,
    "Maryland": 0.297,
    "Massachusetts": 0.270,
    "Michigan": 0.428,
    "Minnesota": 0.351,
    "Nevada": 0.307,
    "New Jersey": 0.217,
    "New York": 0.190,
    "North Carolina": 0.343,
    "Ohio": 0.489,
    "Pennsylvania": 0.336,
    "Tennessee": 0.302,
    "Texas": 0.380,
    "Virginia": 0.298,
    "Washington": 0.076,
}
