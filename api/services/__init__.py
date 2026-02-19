"""
Solar calculation service — unified calculations for all endpoints.
Uses shared constants from solar_constants.py.
"""

from solar_constants import (
    CAPACITY_FACTORS,
    DEFAULT_CAPACITY_FACTOR,
    INSTALL_COST_PER_WATT,
    ITC_RATE,
    ANNUAL_DEGRADATION,
    SYSTEM_LIFETIME_YEARS,
    DEFAULT_DISCOUNT_RATE,
    OM_COST_PER_KW_YEAR,
    GRID_CO2_KG_PER_KWH,
    STATE_CO2_RATES,
    AVG_HOME_KWH_YEAR,
    HOURS_PER_YEAR,
)


def calc_solar(
    area_m2: float,
    state: str,
    usable_pct: float,
    panel_eff: float,
    price: float,
    include_itc: bool = True,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
) -> dict:
    """
    Calculate solar potential for a given roof area with full financial modeling.

    Parameters
    ----------
    area_m2 : float
        Total roof area in square meters.
    state : str
        State name for capacity factor + CO₂ rate lookup.
    usable_pct : float
        Fraction of roof usable for panels (0-1).
    panel_eff : float
        Panel power density in W/m².
    price : float
        Electricity price in $/kWh.
    include_itc : bool
        Whether to apply the 30% federal ITC.
    discount_rate : float
        Discount rate for NPV calculation.

    Returns
    -------
    dict with comprehensive solar generation + financial estimates.
    """
    cf = CAPACITY_FACTORS.get(state, DEFAULT_CAPACITY_FACTOR)
    co2_rate = STATE_CO2_RATES.get(state, GRID_CO2_KG_PER_KWH)

    # --- Generation ---
    usable = area_m2 * usable_pct
    capacity_kw = usable * panel_eff / 1000  # DC nameplate
    annual_kwh_yr1 = capacity_kw * HOURS_PER_YEAR * cf  # year-1 AC output

    # --- Costs ---
    gross_cost = capacity_kw * 1000 * INSTALL_COST_PER_WATT
    itc_savings = gross_cost * ITC_RATE if include_itc else 0.0
    net_cost = gross_cost - itc_savings
    annual_om = capacity_kw * OM_COST_PER_KW_YEAR

    # --- Year-1 financials ---
    annual_revenue_yr1 = annual_kwh_yr1 * price
    net_annual_yr1 = annual_revenue_yr1 - annual_om

    # --- Simple payback (on net cost) ---
    simple_payback = net_cost / net_annual_yr1 if net_annual_yr1 > 0 else 999

    # --- 25-year NPV with degradation ---
    npv = -net_cost
    cumulative_kwh = 0.0
    payback_year = None
    cumulative_cashflow = -net_cost
    yearly_generation = []

    for year in range(1, SYSTEM_LIFETIME_YEARS + 1):
        degradation_factor = (1 - ANNUAL_DEGRADATION) ** (year - 1)
        year_kwh = annual_kwh_yr1 * degradation_factor
        year_revenue = year_kwh * price
        year_cashflow = year_revenue - annual_om
        discounted = year_cashflow / ((1 + discount_rate) ** year)
        npv += discounted
        cumulative_kwh += year_kwh
        cumulative_cashflow += year_cashflow

        if payback_year is None and cumulative_cashflow >= 0:
            payback_year = year

        yearly_generation.append(round(year_kwh / 1000, 1))  # MWh

    lifetime_mwh = cumulative_kwh / 1000

    # --- Environmental ---
    co2_avoided_yr1 = annual_kwh_yr1 * co2_rate / 1000  # metric tons
    co2_avoided_lifetime = cumulative_kwh * co2_rate / 1000
    homes_powered = annual_kwh_yr1 / AVG_HOME_KWH_YEAR

    return {
        # Generation
        "usable_area_m2": round(usable, 1),
        "capacity_kw": round(capacity_kw, 1),
        "capacity_mw": round(capacity_kw / 1000, 3),
        "annual_kwh": round(annual_kwh_yr1, 0),
        "annual_mwh": round(annual_kwh_yr1 / 1000, 1),
        "capacity_factor": cf,
        # Financials
        "annual_revenue": round(annual_revenue_yr1, 0),
        "gross_install_cost": round(gross_cost, 0),
        "itc_savings": round(itc_savings, 0),
        "install_cost": round(net_cost, 0),
        "annual_om": round(annual_om, 0),
        "simple_payback_years": round(simple_payback, 1),
        "payback_years": payback_year or round(simple_payback, 1),
        "npv_25yr": round(npv, 0),
        "lifetime_mwh": round(lifetime_mwh, 0),
        "cost_per_watt": INSTALL_COST_PER_WATT,
        "itc_rate": ITC_RATE if include_itc else 0,
        "discount_rate": discount_rate,
        "degradation_rate": ANNUAL_DEGRADATION,
        "yearly_generation_mwh": yearly_generation,
        # Environmental
        "co2_avoided_tons": round(co2_avoided_yr1, 1),
        "co2_avoided_lifetime_tons": round(co2_avoided_lifetime, 0),
        "homes_powered": round(homes_powered, 0),
        "co2_rate_kg_kwh": co2_rate,
    }


def calc_totals(buildings: list, state: str, usable_pct: float, panel_eff: float, price: float, **kwargs) -> dict:
    """Calculate aggregate totals for a list of buildings."""
    total_area = sum(b["area_m2"] for b in buildings)
    totals = calc_solar(total_area, state, usable_pct, panel_eff, price, **kwargs)
    totals["building_count"] = len(buildings)
    totals["total_roof_area_m2"] = round(total_area, 0)
    return totals
