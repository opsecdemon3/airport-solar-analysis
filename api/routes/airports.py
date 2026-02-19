"""
Airport list and capacity factor endpoints.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services.data_loader import load_airports
from solar_constants import CAPACITY_FACTORS

router = APIRouter(prefix="/api", tags=["airports"])


@router.get("/airports")
def get_airports():
    """Get list of all airports."""
    return load_airports()


@router.get("/capacity-factors")
def get_capacity_factors():
    """Get capacity factors by state (from NREL 2023 ATB)."""
    return JSONResponse(
        content=CAPACITY_FACTORS,
        headers={"Cache-Control": "public, max-age=86400"},
    )
