"""
Building data endpoint — single airport with solar calculations.
"""

import logging
import re

from fastapi import APIRouter, Query, HTTPException

from services import calc_solar, calc_totals
from services.data_loader import load_airports, get_buildings_for_airport

router = APIRouter(prefix="/api", tags=["buildings"])
logger = logging.getLogger(__name__)


@router.get("/buildings/{airport_code}")
def get_buildings(
    airport_code: str,
    radius: float = Query(5, ge=1, le=20, description="Search radius in km"),
    min_size: float = Query(500, ge=100, le=10000, description="Minimum building size m²"),
    usable_pct: float = Query(0.65, ge=0.3, le=0.8, description="Usable roof percentage"),
    panel_eff: float = Query(200, ge=150, le=250, description="Panel efficiency W/m²"),
    elec_price: float = Query(0.12, ge=0.05, le=0.25, description="Electricity price $/kWh"),
    include_itc: bool = Query(True, description="Include 30% federal ITC"),
):
    """Get buildings near an airport with solar calculations."""
    # Validate airport code format (defense-in-depth against path traversal)
    if not re.match(r'^[A-Za-z]{3,4}$', airport_code):
        raise HTTPException(status_code=400, detail="Invalid airport code format")

    airports = load_airports()
    airport = next((a for a in airports if a["code"] == airport_code.upper()), None)
    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport {airport_code} not found")

    buildings, error = get_buildings_for_airport(airport, radius, min_size)

    if error:
        raise HTTPException(status_code=404, detail=error)
    if not buildings:
        return {
            "airport": airport,
            "buildings": [],
            "totals": None,
            "error": "No buildings found",
        }

    # Solar calcs per building
    for b in buildings:
        b["solar"] = calc_solar(
            b["area_m2"], airport["state"], usable_pct, panel_eff, elec_price,
            include_itc=include_itc,
        )

    # Aggregate totals
    totals = calc_totals(
        buildings, airport["state"], usable_pct, panel_eff, elec_price,
        include_itc=include_itc,
    )

    return {
        "airport": airport,
        "buildings": buildings,
        "totals": totals,
        "parameters": {
            "radius_km": radius,
            "min_size_m2": min_size,
            "usable_pct": usable_pct,
            "panel_eff": panel_eff,
            "elec_price": elec_price,
            "include_itc": include_itc,
        },
    }
