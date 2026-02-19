"""
Comprehensive Test Suite for Airport Solar Analysis API
========================================================
Covers every endpoint, parameter combination, edge case, error condition,
solar calculation correctness, data integrity, and middleware behavior.

Run: python3.12 -m pytest tests/test_comprehensive.py -v
"""

import sys
import os
import math
import copy
import json
from pathlib import Path

import pytest
import pytest_asyncio
import httpx

# Add api/ to path so we can import the FastAPI app directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from main import app  # noqa: E402

BASE_URL = "http://testserver"

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="module")
async def client():
    """Async httpx test client — no server needed."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as c:
        yield c


@pytest_asyncio.fixture(scope="module")
async def airports(client):
    """Cache the airport list for the entire module."""
    r = await client.get("/api/airports")
    assert r.status_code == 200
    return r.json()


@pytest_asyncio.fixture(scope="module")
async def atl_buildings(client):
    """Cache a default ATL buildings response."""
    r = await client.get("/api/buildings/ATL", params={"radius": 5, "min_size": 500})
    assert r.status_code == 200
    return r.json()


# ===================================================================
# 1. HEALTH / STATUS / READINESS ENDPOINTS
# ===================================================================

class TestHealthEndpoints:
    """Test all health, status, and readiness endpoints."""

    async def test_health_root(self, client):
        """GET /health returns healthy status."""
        r = await client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    async def test_health_api_prefix(self, client):
        """GET /api/health returns healthy status."""
        r = await client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    async def test_status(self, client):
        """GET /api/status returns operational data."""
        r = await client.get("/api/status")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"
        assert data["version"] == "2.0.0"
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
        assert "start_time" in data
        assert "data" in data
        assert data["data"]["airports_file_exists"] is True
        assert data["data"]["cached_airports"] >= 1

    async def test_ready(self, client):
        """GET /api/ready when system is healthy."""
        r = await client.get("/api/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ready"
        assert "timestamp" in data


# ===================================================================
# 2. AIRPORTS LIST ENDPOINT
# ===================================================================

class TestAirportsEndpoint:
    """Test GET /api/airports."""

    async def test_returns_list(self, airports):
        """Should return a list of airports."""
        assert isinstance(airports, list)
        assert len(airports) == 30

    async def test_airport_fields(self, airports):
        """Each airport has required fields with correct types."""
        for ap in airports:
            assert isinstance(ap["code"], str)
            assert len(ap["code"]) == 3
            assert ap["code"].isupper()
            assert isinstance(ap["name"], str)
            assert len(ap["name"]) > 0
            assert isinstance(ap["lat"], (int, float))
            assert isinstance(ap["lon"], (int, float))
            assert isinstance(ap["state"], str)

    async def test_known_airports_present(self, airports):
        """Top US airports should be in the list."""
        codes = {a["code"] for a in airports}
        for expected in ["ATL", "LAX", "ORD", "DFW", "DEN", "JFK", "SFO", "SEA", "MIA", "BOS"]:
            assert expected in codes, f"{expected} missing from airports list"

    async def test_lat_lon_ranges(self, airports):
        """Lat/lon should be within continental US + Hawaii bounds."""
        for ap in airports:
            assert 18 <= ap["lat"] <= 50, f"{ap['code']} lat out of range: {ap['lat']}"
            assert -160 <= ap["lon"] <= -65, f"{ap['code']} lon out of range: {ap['lon']}"


# ===================================================================
# 3. CAPACITY FACTORS ENDPOINT
# ===================================================================

class TestCapacityFactors:
    """Test GET /api/capacity-factors."""

    async def test_returns_dict(self, client):
        """Should return a dictionary of state -> float."""
        r = await client.get("/api/capacity-factors")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert len(data) >= 20

    async def test_values_in_range(self, client):
        """Capacity factors should be between 0.1 and 0.25."""
        r = await client.get("/api/capacity-factors")
        data = r.json()
        for state, cf in data.items():
            assert 0.10 <= cf <= 0.25, f"{state} CF out of range: {cf}"

    async def test_cache_control_header(self, client):
        """Response should have a cache-control header."""
        r = await client.get("/api/capacity-factors")
        assert "cache-control" in r.headers
        assert "max-age" in r.headers["cache-control"]

    async def test_known_states(self, client):
        """Known high-sun states should have higher CF."""
        r = await client.get("/api/capacity-factors")
        data = r.json()
        assert data.get("Arizona", 0) > data.get("Washington", 0.15)


# ===================================================================
# 4. BUILDINGS ENDPOINT — VALID QUERIES
# ===================================================================

class TestBuildingsValid:
    """Test GET /api/buildings/{code} with valid inputs."""

    async def test_default_params(self, atl_buildings):
        """ATL with default params returns buildings."""
        assert "airport" in atl_buildings
        assert "buildings" in atl_buildings
        assert "totals" in atl_buildings
        assert "parameters" in atl_buildings
        assert len(atl_buildings["buildings"]) > 0

    async def test_airport_object(self, atl_buildings):
        """Airport object has correct fields."""
        ap = atl_buildings["airport"]
        assert ap["code"] == "ATL"
        assert isinstance(ap["name"], str)
        assert isinstance(ap["lat"], (int, float))
        assert isinstance(ap["lon"], (int, float))
        assert isinstance(ap["state"], str)

    async def test_building_structure(self, atl_buildings):
        """Each building has all required fields."""
        for b in atl_buildings["buildings"][:10]:
            assert isinstance(b["area_m2"], (int, float))
            assert b["area_m2"] > 0
            assert isinstance(b["distance_km"], (int, float))
            assert b["distance_km"] >= 0
            assert isinstance(b["lat"], (int, float))
            assert isinstance(b["lon"], (int, float))
            assert "geometry" in b
            assert b["geometry"]["type"] in ("Polygon", "MultiPolygon")

    async def test_solar_calculations_present(self, atl_buildings):
        """Each building has solar calculation results."""
        required_solar_fields = [
            "usable_area_m2", "capacity_kw", "capacity_mw",
            "annual_kwh", "annual_mwh", "capacity_factor",
            "annual_revenue", "gross_install_cost", "itc_savings",
            "install_cost", "annual_om", "simple_payback_years",
            "payback_years", "npv_25yr", "lifetime_mwh",
            "cost_per_watt", "itc_rate", "discount_rate",
            "degradation_rate", "yearly_generation_mwh",
            "co2_avoided_tons", "co2_avoided_lifetime_tons",
            "homes_powered", "co2_rate_kg_kwh",
        ]
        for b in atl_buildings["buildings"][:5]:
            assert "solar" in b
            for field in required_solar_fields:
                assert field in b["solar"], f"Missing solar field: {field}"

    async def test_buildings_sorted_by_area_descending(self, atl_buildings):
        """Buildings should be sorted largest first."""
        areas = [b["area_m2"] for b in atl_buildings["buildings"]]
        for i in range(len(areas) - 1):
            assert areas[i] >= areas[i + 1], f"Not sorted at index {i}: {areas[i]} < {areas[i+1]}"

    async def test_buildings_within_radius(self, atl_buildings):
        """All buildings should be within the requested radius."""
        radius = atl_buildings["parameters"]["radius_km"]
        for b in atl_buildings["buildings"]:
            assert b["distance_km"] <= radius + 0.01, \
                f"Building at {b['distance_km']}km exceeds radius {radius}km"

    async def test_buildings_above_min_size(self, atl_buildings):
        """All buildings should meet minimum size."""
        min_size = atl_buildings["parameters"]["min_size_m2"]
        for b in atl_buildings["buildings"]:
            assert b["area_m2"] >= min_size - 0.1, \
                f"Building {b['area_m2']}m² below min {min_size}m²"

    async def test_totals_structure(self, atl_buildings):
        """Totals should have all fields including building_count."""
        totals = atl_buildings["totals"]
        assert totals is not None
        assert "building_count" in totals
        assert totals["building_count"] == len(atl_buildings["buildings"])
        assert "total_roof_area_m2" in totals
        assert "capacity_mw" in totals
        assert "annual_mwh" in totals
        assert "npv_25yr" in totals

    async def test_parameters_echoed(self, atl_buildings):
        """Response should echo back the request parameters."""
        params = atl_buildings["parameters"]
        assert params["radius_km"] == 5
        assert params["min_size_m2"] == 500
        assert params["usable_pct"] == 0.65
        assert params["panel_eff"] == 200
        assert params["elec_price"] == 0.12
        assert params["include_itc"] is True

    async def test_max_buildings_cap(self, client):
        """Should not return more than MAX_BUILDINGS_RETURN (5000)."""
        r = await client.get("/api/buildings/ATL", params={"radius": 10, "min_size": 100})
        assert r.status_code == 200
        data = r.json()
        assert len(data["buildings"]) <= 5000

    async def test_all_30_airports_return_data(self, client, airports):
        """Every cached airport should return buildings."""
        for ap in airports:
            r = await client.get(f"/api/buildings/{ap['code']}", params={"radius": 5, "min_size": 1000})
            assert r.status_code == 200, f"Failed for {ap['code']}: {r.status_code}"
            data = r.json()
            assert data["airport"]["code"] == ap["code"]
            # Most airports should have buildings with these params
            if len(data["buildings"]) > 0:
                assert data["totals"] is not None
                assert data["totals"]["capacity_mw"] > 0

    async def test_case_insensitive_airport_code(self, client):
        """Airport code should be case-insensitive."""
        r = await client.get("/api/buildings/atl", params={"radius": 3, "min_size": 1000})
        assert r.status_code == 200
        assert r.json()["airport"]["code"] == "ATL"


# ===================================================================
# 5. BUILDINGS ENDPOINT — PARAMETER VARIATIONS
# ===================================================================

class TestBuildingsParams:
    """Test buildings endpoint with various parameter combinations."""

    async def test_small_radius(self, client):
        """Radius=1 should return fewer buildings."""
        r = await client.get("/api/buildings/ATL", params={"radius": 1, "min_size": 500})
        assert r.status_code == 200
        data = r.json()
        assert len(data["buildings"]) < 500  # ATL within 1km is small

    async def test_large_radius(self, client):
        """Radius=10 should return more buildings."""
        r = await client.get("/api/buildings/ATL", params={"radius": 10, "min_size": 500})
        assert r.status_code == 200
        data = r.json()
        assert len(data["buildings"]) > 500

    async def test_high_min_size(self, client):
        """Large min_size filters down to only big buildings."""
        r = await client.get("/api/buildings/ATL", params={"radius": 5, "min_size": 5000})
        assert r.status_code == 200
        data = r.json()
        for b in data["buildings"]:
            assert b["area_m2"] >= 5000

    async def test_low_min_size(self, client):
        """Low min_size returns more buildings."""
        r_low = await client.get("/api/buildings/ATL", params={"radius": 5, "min_size": 200})
        r_high = await client.get("/api/buildings/ATL", params={"radius": 5, "min_size": 2000})
        assert len(r_low.json()["buildings"]) > len(r_high.json()["buildings"])

    async def test_usable_pct_affects_capacity(self, client):
        """Changing usable_pct should change solar calculations."""
        r1 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "usable_pct": 0.3})
        r2 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "usable_pct": 0.8})
        b1 = r1.json()["buildings"][0]["solar"]
        b2 = r2.json()["buildings"][0]["solar"]
        assert b2["capacity_kw"] > b1["capacity_kw"]
        assert b2["annual_mwh"] > b1["annual_mwh"]

    async def test_panel_eff_affects_capacity(self, client):
        """Changing panel_eff should change solar calculations."""
        r1 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "panel_eff": 150})
        r2 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "panel_eff": 250})
        b1 = r1.json()["buildings"][0]["solar"]
        b2 = r2.json()["buildings"][0]["solar"]
        assert b2["capacity_kw"] > b1["capacity_kw"]

    async def test_elec_price_affects_revenue(self, client):
        """Changing electricity price should change revenue but not capacity."""
        r1 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "elec_price": 0.06})
        r2 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "elec_price": 0.25})
        b1 = r1.json()["buildings"][0]["solar"]
        b2 = r2.json()["buildings"][0]["solar"]
        assert b1["capacity_kw"] == b2["capacity_kw"]  # Same capacity
        assert b2["annual_revenue"] > b1["annual_revenue"]  # Higher revenue
        assert b2["npv_25yr"] > b1["npv_25yr"]  # Higher NPV

    async def test_include_itc_false(self, client):
        """Disabling ITC should increase install cost and worsen payback."""
        r1 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "include_itc": True})
        r2 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "include_itc": False})
        s1 = r1.json()["buildings"][0]["solar"]
        s2 = r2.json()["buildings"][0]["solar"]
        assert s2["itc_savings"] == 0
        assert s2["itc_rate"] == 0
        assert s2["install_cost"] > s1["install_cost"]
        assert s2["install_cost"] == s2["gross_install_cost"]
        assert s1["install_cost"] < s1["gross_install_cost"]

    async def test_no_itc_higher_payback(self, client):
        """Without ITC, payback should be longer."""
        r1 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "include_itc": True})
        r2 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "include_itc": False})
        s1 = r1.json()["buildings"][0]["solar"]
        s2 = r2.json()["buildings"][0]["solar"]
        assert s2["payback_years"] >= s1["payback_years"]

    async def test_same_params_same_results(self, client):
        """Identical requests should return identical results (cache correctness)."""
        params = {"radius": 3, "min_size": 2000, "usable_pct": 0.5, "panel_eff": 180, "elec_price": 0.15}
        r1 = await client.get("/api/buildings/ATL", params=params)
        r2 = await client.get("/api/buildings/ATL", params=params)
        d1 = r1.json()
        d2 = r2.json()
        assert len(d1["buildings"]) == len(d2["buildings"])
        for b1, b2 in zip(d1["buildings"][:5], d2["buildings"][:5]):
            assert b1["solar"]["capacity_kw"] == b2["solar"]["capacity_kw"]
            assert b1["solar"]["annual_mwh"] == b2["solar"]["annual_mwh"]

    async def test_cache_not_mutated_across_requests(self, client):
        """Different solar params should give different results (cache mutation fix)."""
        r1 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "usable_pct": 0.3})
        r2 = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000, "usable_pct": 0.8})
        s1 = r1.json()["buildings"][0]["solar"]
        s2 = r2.json()["buildings"][0]["solar"]
        # These MUST be different — the old bug had them being the same
        assert s1["capacity_kw"] != s2["capacity_kw"], \
            "Cache mutation bug: solar calcs should differ with different usable_pct"
        assert abs(s2["capacity_kw"] / s1["capacity_kw"] - 0.8 / 0.3) < 0.01

    async def test_different_airport_different_capacity_factor(self, client):
        """Airports in different states should have different capacity factors."""
        r_atl = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000})
        r_phx = await client.get("/api/buildings/PHX", params={"radius": 3, "min_size": 5000})
        cf_atl = r_atl.json()["buildings"][0]["solar"]["capacity_factor"]
        cf_phx = r_phx.json()["buildings"][0]["solar"]["capacity_factor"]
        assert cf_phx > cf_atl  # Arizona has more sun than Georgia


# ===================================================================
# 6. BUILDINGS ENDPOINT — ERROR CONDITIONS
# ===================================================================

class TestBuildingsErrors:
    """Test buildings endpoint error handling."""

    async def test_invalid_airport_code_format(self, client):
        """Non-alpha or wrong length codes should return 400."""
        bad_codes = ["12", "ABCDE", "A1B", "../../etc", "AB", ""]
        for code in bad_codes:
            r = await client.get(f"/api/buildings/{code}")
            assert r.status_code in (400, 404, 405, 422), \
                f"Expected error for code '{code}', got {r.status_code}"

    async def test_path_traversal_blocked(self, client):
        """Path traversal attempts should be rejected."""
        r = await client.get("/api/buildings/..%2F..%2Fetc")
        assert r.status_code in (400, 404, 422)

    async def test_unknown_airport_code(self, client):
        """Valid format but unknown code should return 404."""
        r = await client.get("/api/buildings/ZZZ")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    async def test_radius_below_min(self, client):
        """Radius below minimum should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"radius": 0})
        assert r.status_code == 422

    async def test_radius_above_max(self, client):
        """Radius above maximum should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"radius": 100})
        assert r.status_code == 422

    async def test_min_size_below_min(self, client):
        """Min size below minimum should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"min_size": 10})
        assert r.status_code == 422

    async def test_min_size_above_max(self, client):
        """Min size above maximum should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"min_size": 100000})
        assert r.status_code == 422

    async def test_usable_pct_below_min(self, client):
        """Usable pct below 0.3 should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"usable_pct": 0.1})
        assert r.status_code == 422

    async def test_usable_pct_above_max(self, client):
        """Usable pct above 0.8 should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"usable_pct": 1.5})
        assert r.status_code == 422

    async def test_panel_eff_below_min(self, client):
        """Panel efficiency below 150 should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"panel_eff": 50})
        assert r.status_code == 422

    async def test_panel_eff_above_max(self, client):
        """Panel efficiency above 250 should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"panel_eff": 500})
        assert r.status_code == 422

    async def test_elec_price_below_min(self, client):
        """Electricity price below 0.05 should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"elec_price": 0.01})
        assert r.status_code == 422

    async def test_elec_price_above_max(self, client):
        """Electricity price above 0.25 should be rejected."""
        r = await client.get("/api/buildings/ATL", params={"elec_price": 1.0})
        assert r.status_code == 422

    async def test_very_high_min_size_no_buildings(self, client):
        """Very high min_size should return empty buildings with 200."""
        r = await client.get("/api/buildings/ATL", params={"min_size": 10000, "radius": 1})
        assert r.status_code == 200
        data = r.json()
        # Might have 0 buildings this close with this min_size
        assert isinstance(data["buildings"], list)


# ===================================================================
# 7. COMPARE ENDPOINT
# ===================================================================

class TestCompareEndpoint:
    """Test GET /api/compare."""

    async def test_compare_two_airports(self, client):
        """Compare two airports returns results for both."""
        r = await client.get("/api/compare", params={"codes": "ATL,JFK"})
        assert r.status_code == 200
        data = r.json()
        assert "airports" in data
        assert "parameters" in data
        assert len(data["airports"]) == 2
        codes = {a["code"] for a in data["airports"]}
        assert codes == {"ATL", "JFK"}

    async def test_compare_result_structure(self, client):
        """Each airport in compare response has expected fields."""
        r = await client.get("/api/compare", params={"codes": "ATL,LAX"})
        data = r.json()
        for airport_result in data["airports"]:
            assert "code" in airport_result
            if "error" not in airport_result:
                assert "airport" in airport_result
                assert "totals" in airport_result
                assert "building_count" in airport_result
                assert airport_result["building_count"] > 0
                totals = airport_result["totals"]
                assert "capacity_mw" in totals
                assert "annual_mwh" in totals
                assert "npv_25yr" in totals

    async def test_compare_max_8_airports(self, client):
        """Should cap at 8 airports even if more requested."""
        codes = "ATL,JFK,LAX,ORD,DFW,DEN,SFO,SEA,MIA,BOS"
        r = await client.get("/api/compare", params={"codes": codes})
        assert r.status_code == 200
        data = r.json()
        assert len(data["airports"]) <= 8

    async def test_compare_unknown_airport(self, client):
        """Unknown airport in compare returns error for that entry."""
        r = await client.get("/api/compare", params={"codes": "ATL,ZZZ"})
        assert r.status_code == 200
        data = r.json()
        assert len(data["airports"]) == 2
        # ATL should succeed
        atl = next(a for a in data["airports"] if a["code"] == "ATL")
        assert "totals" in atl
        # ZZZ should have error
        zzz = next(a for a in data["airports"] if a["code"] == "ZZZ")
        assert "error" in zzz

    async def test_compare_no_codes(self, client):
        """Missing codes parameter should fail."""
        r = await client.get("/api/compare")
        assert r.status_code == 422  # required param missing

    async def test_compare_empty_codes(self, client):
        """Empty codes string should return 400."""
        r = await client.get("/api/compare", params={"codes": ""})
        assert r.status_code == 400

    async def test_compare_invalid_codes(self, client):
        """All invalid codes should return 400."""
        r = await client.get("/api/compare", params={"codes": "123,456"})
        assert r.status_code == 400

    async def test_compare_with_solar_params(self, client):
        """Compare should respect custom solar parameters."""
        r = await client.get("/api/compare", params={
            "codes": "ATL,JFK",
            "usable_pct": 0.4,
            "panel_eff": 180,
            "elec_price": 0.20,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["parameters"]["usable_pct"] == 0.4
        assert data["parameters"]["panel_eff"] == 180
        assert data["parameters"]["elec_price"] == 0.20

    async def test_compare_single_airport(self, client):
        """Compare with a single airport should work."""
        r = await client.get("/api/compare", params={"codes": "ATL"})
        assert r.status_code == 200
        assert len(r.json()["airports"]) == 1


# ===================================================================
# 8. AGGREGATE ENDPOINT
# ===================================================================

class TestAggregateEndpoint:
    """Test GET /api/aggregate."""

    async def test_aggregate_response_structure(self, client):
        """Aggregate response has airports array and totals."""
        r = await client.get("/api/aggregate", params={"min_size": 2000})
        assert r.status_code == 200
        data = r.json()
        assert "airports" in data
        assert "totals" in data
        assert isinstance(data["airports"], list)

    async def test_aggregate_totals(self, client):
        """Aggregate totals should have expected fields."""
        r = await client.get("/api/aggregate", params={"min_size": 2000})
        data = r.json()
        totals = data["totals"]
        assert "airport_count" in totals
        assert "building_count" in totals
        assert "capacity_mw" in totals
        assert "annual_mwh" in totals
        assert "annual_revenue" in totals
        assert "co2_avoided_tons" in totals
        assert "homes_powered" in totals

    async def test_aggregate_all_airports_included(self, client):
        """Aggregate should include most/all 30 airports."""
        r = await client.get("/api/aggregate", params={"min_size": 1000})
        data = r.json()
        assert data["totals"]["airport_count"] >= 25  # Allow some flexibility

    async def test_aggregate_per_airport_fields(self, client):
        """Each airport in aggregate has expected fields."""
        r = await client.get("/api/aggregate", params={"min_size": 2000})
        data = r.json()
        for ap in data["airports"][:5]:
            assert "code" in ap
            assert "name" in ap
            assert "state" in ap
            assert "buildings" in ap
            assert "capacity_mw" in ap
            assert "annual_mwh" in ap
            assert "annual_revenue" in ap
            assert "co2_avoided_tons" in ap
            assert "payback_years" in ap
            assert "npv_25yr" in ap

    async def test_aggregate_sorted_by_energy(self, client):
        """Airports should be sorted by annual_mwh descending."""
        r = await client.get("/api/aggregate", params={"min_size": 2000})
        data = r.json()
        mwh_values = [ap["annual_mwh"] for ap in data["airports"]]
        for i in range(len(mwh_values) - 1):
            assert mwh_values[i] >= mwh_values[i + 1], \
                f"Not sorted at index {i}: {mwh_values[i]} < {mwh_values[i+1]}"

    async def test_aggregate_totals_consistency(self, client):
        """Aggregate totals should be sum of individual airport values."""
        r = await client.get("/api/aggregate", params={"min_size": 2000})
        data = r.json()
        sum_buildings = sum(ap["buildings"] for ap in data["airports"])
        sum_capacity = sum(ap["capacity_mw"] for ap in data["airports"])
        assert data["totals"]["building_count"] == sum_buildings
        assert abs(data["totals"]["capacity_mw"] - round(sum_capacity, 1)) < 1.0

    async def test_aggregate_homes_powered_formula(self, client):
        """homes_powered should equal total_mwh * 1000 / 10500."""
        r = await client.get("/api/aggregate", params={"min_size": 2000})
        data = r.json()
        expected_homes = int(data["totals"]["annual_mwh"] * 1000 / 10500)
        assert abs(data["totals"]["homes_powered"] - expected_homes) <= 1

    async def test_aggregate_with_custom_params(self, client):
        """Aggregate should respect custom solar parameters."""
        r1 = await client.get("/api/aggregate", params={"min_size": 5000, "elec_price": 0.06})
        r2 = await client.get("/api/aggregate", params={"min_size": 5000, "elec_price": 0.25})
        t1 = r1.json()["totals"]
        t2 = r2.json()["totals"]
        # Same building count (same radius/min_size) but different financials
        assert t1["building_count"] == t2["building_count"]
        assert t2["annual_revenue"] > t1["annual_revenue"]


# ===================================================================
# 9. SOLAR CALCULATION CORRECTNESS
# ===================================================================

class TestSolarCalculations:
    """Verify solar calculation math is correct."""

    async def test_capacity_formula(self, atl_buildings):
        """capacity_kw = usable_area * panel_eff / 1000."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["usable_area_m2"] * 200 / 1000  # default panel_eff=200
        assert abs(s["capacity_kw"] - round(expected, 1)) < 0.2

    async def test_usable_area_formula(self, atl_buildings):
        """usable_area = area_m2 * usable_pct."""
        b = atl_buildings["buildings"][0]
        expected = b["area_m2"] * 0.65  # default usable_pct
        assert abs(b["solar"]["usable_area_m2"] - round(expected, 1)) < 0.2

    async def test_annual_kwh_formula(self, atl_buildings):
        """annual_kwh = capacity_kw * 8760 * capacity_factor."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["capacity_kw"] * 8760 * s["capacity_factor"]
        assert abs(s["annual_kwh"] - round(expected, 0)) < 100

    async def test_annual_mwh_matches_kwh(self, atl_buildings):
        """annual_mwh = annual_kwh / 1000."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        assert abs(s["annual_mwh"] - round(s["annual_kwh"] / 1000, 1)) < 0.2

    async def test_gross_install_cost(self, atl_buildings):
        """gross_install_cost = capacity_kw * 1000 * $1.40/W."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["capacity_kw"] * 1000 * 1.40
        assert abs(s["gross_install_cost"] - round(expected, 0)) < 100

    async def test_itc_savings(self, atl_buildings):
        """itc_savings = gross_install_cost * 0.30."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["gross_install_cost"] * 0.30
        assert abs(s["itc_savings"] - round(expected, 0)) < 10

    async def test_net_install_cost(self, atl_buildings):
        """install_cost = gross_install_cost - itc_savings."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["gross_install_cost"] - s["itc_savings"]
        assert abs(s["install_cost"] - round(expected, 0)) < 10

    async def test_annual_revenue(self, atl_buildings):
        """annual_revenue = annual_kwh * elec_price."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["annual_kwh"] * 0.12  # default price
        assert abs(s["annual_revenue"] - round(expected, 0)) < 100

    async def test_annual_om(self, atl_buildings):
        """annual_om = capacity_kw * $15/kW."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["capacity_kw"] * 15
        assert abs(s["annual_om"] - round(expected, 0)) < 10

    async def test_yearly_generation_25_entries(self, atl_buildings):
        """yearly_generation_mwh should have exactly 25 entries."""
        b = atl_buildings["buildings"][0]
        assert len(b["solar"]["yearly_generation_mwh"]) == 25

    async def test_yearly_generation_degrades(self, atl_buildings):
        """Each year's generation should be slightly less than the previous."""
        b = atl_buildings["buildings"][0]
        gen = b["solar"]["yearly_generation_mwh"]
        for i in range(1, len(gen)):
            assert gen[i] <= gen[i - 1], f"Year {i+1} ({gen[i]}) > year {i} ({gen[i-1]})"

    async def test_degradation_rate(self, atl_buildings):
        """Year 25 generation should be ~88.8% of year 1 (0.995^24)."""
        b = atl_buildings["buildings"][0]
        gen = b["solar"]["yearly_generation_mwh"]
        expected_ratio = 0.995 ** 24  # ~0.8864
        actual_ratio = gen[24] / gen[0] if gen[0] > 0 else 0
        assert abs(actual_ratio - expected_ratio) < 0.01

    async def test_co2_calculation(self, atl_buildings):
        """co2_avoided = annual_kwh * co2_rate / 1000."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["annual_kwh"] * s["co2_rate_kg_kwh"] / 1000
        assert abs(s["co2_avoided_tons"] - round(expected, 1)) < 0.2

    async def test_homes_powered(self, atl_buildings):
        """homes_powered = annual_kwh / 10500."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["annual_kwh"] / 10500
        assert abs(s["homes_powered"] - round(expected, 0)) < 2

    async def test_npv_is_positive_for_large_buildings(self, atl_buildings):
        """Large buildings (5000+ m²) should have positive NPV."""
        for b in atl_buildings["buildings"][:10]:
            if b["area_m2"] > 5000:
                assert b["solar"]["npv_25yr"] > 0, \
                    f"NPV should be positive for {b['area_m2']}m² building"

    async def test_payback_under_25_years(self, atl_buildings):
        """Most buildings should have payback < 25 years at defaults."""
        paybacks = [b["solar"]["payback_years"] for b in atl_buildings["buildings"][:20]]
        reasonable = sum(1 for p in paybacks if p < 25)
        assert reasonable >= 15, f"Only {reasonable}/20 buildings have payback < 25yr"

    async def test_capacity_conversion(self, atl_buildings):
        """capacity_mw should equal capacity_kw / 1000."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        assert abs(s["capacity_mw"] - round(s["capacity_kw"] / 1000, 3)) < 0.001

    async def test_lifetime_mwh_reasonable(self, atl_buildings):
        """Lifetime MWh should be roughly 25 * annual_mwh (minus degradation)."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        # With 0.5%/yr degradation, lifetime factor ≈ 23.85×
        expected_factor = sum((0.995 ** (y - 1)) for y in range(1, 26))
        expected = s["annual_mwh"] * expected_factor
        assert abs(s["lifetime_mwh"] - round(expected, 0)) < 50


# ===================================================================
# 10. DATA INTEGRITY
# ===================================================================

class TestDataIntegrity:
    """Test data quality and integrity across airports."""

    async def test_no_duplicate_buildings(self, client):
        """Buildings should not have near-identical coordinates (dup check)."""
        r = await client.get("/api/buildings/ATL", params={"radius": 5, "min_size": 500})
        buildings = r.json()["buildings"]
        # Check for exact lat/lon duplicates
        coords = [(b["lat"], b["lon"]) for b in buildings]
        unique = set(coords)
        dup_rate = 1 - len(unique) / len(coords) if coords else 0
        assert dup_rate < 0.01, f"Too many exact coordinate duplicates: {dup_rate:.1%}"

    async def test_building_coordinates_near_airport(self, client, airports):
        """Building lat/lon should be geographically near their airport."""
        for code in ["ATL", "JFK", "LAX"]:
            ap = next(a for a in airports if a["code"] == code)
            r = await client.get(f"/api/buildings/{code}", params={"radius": 5, "min_size": 1000})
            for b in r.json()["buildings"][:20]:
                # Rough check: should be within ~0.15 degrees (~15km)
                assert abs(b["lat"] - ap["lat"]) < 0.15, \
                    f"{code}: building lat {b['lat']} too far from airport {ap['lat']}"
                assert abs(b["lon"] - ap["lon"]) < 0.15, \
                    f"{code}: building lon {b['lon']} too far from airport {ap['lon']}"

    async def test_building_areas_reasonable(self, client):
        """Building areas should be in a reasonable range."""
        r = await client.get("/api/buildings/ATL", params={"radius": 5, "min_size": 500})
        for b in r.json()["buildings"]:
            assert 100 <= b["area_m2"] <= 1_000_000, \
                f"Unreasonable area: {b['area_m2']}m²"

    async def test_geometry_valid(self, atl_buildings):
        """Building geometries should be valid GeoJSON."""
        for b in atl_buildings["buildings"][:20]:
            geom = b["geometry"]
            assert geom["type"] in ("Polygon", "MultiPolygon")
            assert "coordinates" in geom
            if geom["type"] == "Polygon":
                # At least one ring with at least 4 points (closed)
                assert len(geom["coordinates"]) >= 1
                assert len(geom["coordinates"][0]) >= 4

    async def test_large_airports_have_many_buildings(self, client):
        """Major airports should have substantial building counts."""
        for code in ["ATL", "LAX", "ORD", "DFW"]:
            r = await client.get(f"/api/buildings/{code}", params={"radius": 5, "min_size": 500})
            count = len(r.json()["buildings"])
            assert count >= 100, f"{code} only has {count} buildings at 5km/500m²"

    async def test_total_roof_area_sums_correctly(self, atl_buildings):
        """Totals roof area should equal sum of building areas."""
        total = atl_buildings["totals"]["total_roof_area_m2"]
        summed = sum(b["area_m2"] for b in atl_buildings["buildings"])
        assert abs(total - round(summed, 0)) < 10


# ===================================================================
# 11. MIDDLEWARE — HEADERS
# ===================================================================

class TestMiddleware:
    """Test middleware behavior: security headers, timing, CORS."""

    async def test_security_headers(self, client):
        """Response should contain security headers."""
        r = await client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"

    async def test_timing_header(self, client):
        """Response should contain process time header."""
        r = await client.get("/health")
        assert "x-process-time" in r.headers
        raw = r.headers["x-process-time"].replace("ms", "").replace("s", "")
        proc_time = float(raw)
        assert proc_time >= 0

    async def test_cors_headers(self, client):
        """CORS preflight should be handled."""
        r = await client.options("/api/airports", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        # Should not be 405 Method Not Allowed
        assert r.status_code in (200, 204)


# ===================================================================
# 12. EDGE CASES & BOUNDARY CONDITIONS
# ===================================================================

class TestEdgeCases:
    """Test boundary conditions and unusual inputs."""

    async def test_minimum_valid_params(self, client):
        """All params at their minimum valid values."""
        r = await client.get("/api/buildings/ATL", params={
            "radius": 1, "min_size": 100,
            "usable_pct": 0.3, "panel_eff": 150, "elec_price": 0.05,
        })
        assert r.status_code == 200

    async def test_maximum_valid_params(self, client):
        """All params at their maximum valid values."""
        r = await client.get("/api/buildings/ATL", params={
            "radius": 20, "min_size": 10000,
            "usable_pct": 0.8, "panel_eff": 250, "elec_price": 0.25,
        })
        assert r.status_code == 200

    async def test_float_radius(self, client):
        """Fractional radius should work."""
        r = await client.get("/api/buildings/ATL", params={"radius": 3.5})
        assert r.status_code == 200

    async def test_non_existent_endpoint(self, client):
        """Unknown endpoint should return 404."""
        r = await client.get("/api/nonexistent")
        assert r.status_code == 404

    async def test_post_not_allowed(self, client):
        """POST to a GET endpoint should return 405."""
        r = await client.post("/api/airports")
        assert r.status_code == 405

    async def test_building_with_no_solar_edge(self, client):
        """Buildings with very small area should still get valid solar calcs."""
        r = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 100})
        assert r.status_code == 200
        data = r.json()
        if data["buildings"]:
            # Even smallest building should have non-negative solar values
            b = data["buildings"][-1]
            assert b["solar"]["capacity_kw"] >= 0
            assert b["solar"]["annual_mwh"] >= 0
            assert b["solar"]["npv_25yr"] is not None

    async def test_hawaii_airport(self, client):
        """HNL (Hawaii) should work with correct timezone/projection."""
        r = await client.get("/api/buildings/HNL", params={"radius": 5, "min_size": 1000})
        assert r.status_code == 200
        data = r.json()
        assert data["airport"]["code"] == "HNL"
        # Hawaii has buildings
        if len(data["buildings"]) > 0:
            assert data["buildings"][0]["solar"]["capacity_factor"] > 0

    async def test_concurrent_different_params(self, client):
        """Back-to-back requests with different params should not interfere."""
        results = []
        for pct in [0.3, 0.5, 0.7]:
            r = await client.get("/api/buildings/JFK", params={
                "radius": 3, "min_size": 5000, "usable_pct": pct
            })
            assert r.status_code == 200
            b0 = r.json()["buildings"][0]["solar"]
            results.append((pct, b0["capacity_kw"]))

        # Capacity should scale linearly with usable_pct
        for i in range(len(results) - 1):
            pct1, cap1 = results[i]
            pct2, cap2 = results[i + 1]
            expected_ratio = pct2 / pct1
            actual_ratio = cap2 / cap1
            assert abs(actual_ratio - expected_ratio) < 0.01, \
                f"Capacity didn't scale: {pct1}->{pct2}, expected {expected_ratio:.3f}, got {actual_ratio:.3f}"


# ===================================================================
# 13. SOLAR CONSTANTS VALIDATION
# ===================================================================

class TestSolarConstants:
    """Verify solar constants are reasonable and consistent."""

    async def test_capacity_factors_request(self, client):
        """All capacity factors from the API should be consistent."""
        r = await client.get("/api/capacity-factors")
        data = r.json()
        # Arizona should be among highest, Washington among lowest
        assert data.get("Arizona", 0) >= 0.18
        assert data.get("Georgia", 0) >= 0.15  # ATL's state

    async def test_cost_per_watt(self, atl_buildings):
        """Cost per watt should be $1.40."""
        s = atl_buildings["buildings"][0]["solar"]
        assert s["cost_per_watt"] == 1.40

    async def test_discount_rate(self, atl_buildings):
        """Default discount rate should be 6%."""
        s = atl_buildings["buildings"][0]["solar"]
        assert s["discount_rate"] == 0.06

    async def test_degradation_rate(self, atl_buildings):
        """Degradation rate should be 0.5%."""
        s = atl_buildings["buildings"][0]["solar"]
        assert s["degradation_rate"] == 0.005

    async def test_itc_rate_with_itc(self, atl_buildings):
        """ITC rate should be 30% when enabled."""
        s = atl_buildings["buildings"][0]["solar"]
        assert s["itc_rate"] == 0.30


# ===================================================================
# 14. RESPONSE FORMAT & TYPES
# ===================================================================

class TestResponseFormats:
    """Verify response types are consistent and serializable."""

    async def test_all_numbers_are_finite(self, atl_buildings):
        """No NaN or Infinity in any numeric field."""
        for b in atl_buildings["buildings"][:20]:
            for key, val in b["solar"].items():
                if isinstance(val, (int, float)):
                    assert math.isfinite(val), f"Non-finite value: {key}={val}"
                elif isinstance(val, list):
                    for v in val:
                        if isinstance(v, (int, float)):
                            assert math.isfinite(v), f"Non-finite in {key}: {v}"

    async def test_response_is_json_serializable(self, atl_buildings):
        """Full response should be JSON-serializable."""
        serialized = json.dumps(atl_buildings)
        deserialized = json.loads(serialized)
        assert len(deserialized["buildings"]) == len(atl_buildings["buildings"])

    async def test_no_none_in_critical_fields(self, atl_buildings):
        """Critical fields should never be None."""
        for b in atl_buildings["buildings"][:20]:
            assert b["area_m2"] is not None
            assert b["distance_km"] is not None
            assert b["lat"] is not None
            assert b["lon"] is not None
            assert b["solar"]["capacity_kw"] is not None
            assert b["solar"]["annual_mwh"] is not None
            assert b["solar"]["npv_25yr"] is not None

    async def test_content_type_json(self, client):
        """All API responses should be application/json."""
        for path in ["/health", "/api/airports", "/api/capacity-factors",
                     "/api/buildings/ATL?radius=3&min_size=5000",
                     "/api/compare?codes=ATL,JFK&min_size=5000",
                     "/api/status"]:
            r = await client.get(path)
            assert "application/json" in r.headers.get("content-type", ""), \
                f"{path} returned content-type: {r.headers.get('content-type')}"


# ===================================================================
# 15. UNIT TESTS — SOLAR CALC FUNCTION DIRECTLY
# ===================================================================

class TestSolarCalcUnit:
    """Test calc_solar() directly with known inputs — no HTTP."""

    def test_known_area_georgia(self):
        """Verify exact values for a 10,000 m² roof in Georgia."""
        from services import calc_solar
        result = calc_solar(
            area_m2=10000, state="Georgia",
            usable_pct=0.65, panel_eff=200, price=0.12,
            include_itc=True,
        )
        # usable = 10000 * 0.65 = 6500 m²
        assert result["usable_area_m2"] == 6500.0
        # capacity = 6500 * 200 / 1000 = 1300 kW
        assert result["capacity_kw"] == 1300.0
        assert result["capacity_mw"] == 1.3
        # CF for Georgia = 0.168
        assert result["capacity_factor"] == 0.168
        # annual kWh = 1300 * 8760 * 0.168 = 1,913,184
        expected_kwh = 1300 * 8760 * 0.168
        assert abs(result["annual_kwh"] - round(expected_kwh, 0)) < 1
        # gross cost = 1300 * 1000 * 1.40 = $1,820,000
        assert result["gross_install_cost"] == 1_820_000
        # ITC = $546,000
        assert result["itc_savings"] == 546_000
        # net cost = $1,274,000
        assert result["install_cost"] == 1_274_000

    def test_zero_area(self):
        """Zero area should produce all-zero generation."""
        from services import calc_solar
        result = calc_solar(area_m2=0, state="Georgia",
                            usable_pct=0.65, panel_eff=200, price=0.12)
        assert result["capacity_kw"] == 0
        assert result["annual_mwh"] == 0
        assert result["gross_install_cost"] == 0

    def test_unknown_state_uses_default_cf(self):
        """Unknown state should fall back to DEFAULT_CAPACITY_FACTOR = 0.158."""
        from services import calc_solar
        result = calc_solar(area_m2=1000, state="Narnia",
                            usable_pct=0.65, panel_eff=200, price=0.12)
        assert result["capacity_factor"] == 0.158

    def test_unknown_state_uses_default_co2(self):
        """Unknown state should fall back to default CO2 rate = 0.386."""
        from services import calc_solar
        result = calc_solar(area_m2=1000, state="Narnia",
                            usable_pct=0.65, panel_eff=200, price=0.12)
        assert result["co2_rate_kg_kwh"] == 0.386

    def test_npv_manual_25yr(self):
        """Manually verify NPV by computing the full 25-year DCF."""
        from services import calc_solar
        result = calc_solar(area_m2=5000, state="Arizona",
                            usable_pct=0.65, panel_eff=200, price=0.12,
                            include_itc=True, discount_rate=0.06)
        # Reproduce NPV
        capacity_kw = 5000 * 0.65 * 200 / 1000  # 650 kW
        annual_kwh_yr1 = capacity_kw * 8760 * 0.198
        gross_cost = capacity_kw * 1000 * 1.40
        net_cost = gross_cost - gross_cost * 0.30
        annual_om = capacity_kw * 15
        npv = -net_cost
        for year in range(1, 26):
            deg = (1 - 0.005) ** (year - 1)
            yr_kwh = annual_kwh_yr1 * deg
            yr_rev = yr_kwh * 0.12
            yr_cf = yr_rev - annual_om
            npv += yr_cf / (1.06 ** year)
        assert abs(result["npv_25yr"] - round(npv, 0)) < 2

    def test_simple_payback_vs_discounted(self):
        """Simple payback should always be <= discounted payback."""
        from services import calc_solar
        result = calc_solar(area_m2=5000, state="Arizona",
                            usable_pct=0.65, panel_eff=200, price=0.12)
        assert result["simple_payback_years"] <= result["payback_years"]

    def test_calc_totals_sums_correctly(self):
        """calc_totals should run on sum of all building areas."""
        from services import calc_solar, calc_totals
        buildings = [{"area_m2": 1000}, {"area_m2": 2000}, {"area_m2": 3000}]
        totals = calc_totals(buildings, "Georgia", 0.65, 200, 0.12)
        # Should use total area = 6000
        single = calc_solar(6000, "Georgia", 0.65, 200, 0.12)
        assert totals["capacity_kw"] == single["capacity_kw"]
        assert totals["annual_mwh"] == single["annual_mwh"]
        assert totals["building_count"] == 3
        assert totals["total_roof_area_m2"] == 6000


# ===================================================================
# 16. CROSS-ENDPOINT CONSISTENCY
# ===================================================================

class TestCrossEndpointConsistency:
    """Verify data consistency across different endpoints."""

    async def test_buildings_totals_match_compare(self, client):
        """Buildings endpoint totals should match compare endpoint for same airport."""
        b_resp = await client.get("/api/buildings/ATL", params={
            "radius": 5, "min_size": 2000, "usable_pct": 0.65,
            "panel_eff": 200, "elec_price": 0.12, "include_itc": True,
        })
        c_resp = await client.get("/api/compare", params={
            "codes": "ATL", "radius": 5, "min_size": 2000,
            "usable_pct": 0.65, "panel_eff": 200, "elec_price": 0.12,
            "include_itc": True,
        })
        b_data = b_resp.json()
        c_data = c_resp.json()
        atl_compare = c_data["airports"][0]

        assert b_data["totals"]["capacity_mw"] == atl_compare["totals"]["capacity_mw"]
        assert b_data["totals"]["annual_mwh"] == atl_compare["totals"]["annual_mwh"]
        assert b_data["totals"]["building_count"] == atl_compare["building_count"]

    async def test_airport_in_buildings_matches_list(self, client, airports):
        """Airport metadata in buildings response should match /api/airports."""
        r = await client.get("/api/buildings/JFK", params={"radius": 3, "min_size": 5000})
        b_airport = r.json()["airport"]
        jfk = next(a for a in airports if a["code"] == "JFK")
        assert b_airport["code"] == jfk["code"]
        assert b_airport["name"] == jfk["name"]
        assert b_airport["lat"] == jfk["lat"]
        assert b_airport["lon"] == jfk["lon"]
        assert b_airport["state"] == jfk["state"]

    async def test_capacity_factor_matches_constants(self, client):
        """Building solar CF should match the /api/capacity-factors endpoint."""
        cf_resp = await client.get("/api/capacity-factors")
        cf_map = cf_resp.json()

        b_resp = await client.get("/api/buildings/ATL", params={"radius": 3, "min_size": 5000})
        data = b_resp.json()
        state = data["airport"]["state"]
        building_cf = data["buildings"][0]["solar"]["capacity_factor"]
        assert building_cf == cf_map[state]

    async def test_status_requests_increment(self, client):
        """requests_handled should increase between status checks."""
        r1 = await client.get("/api/status")
        count1 = r1.json()["requests_handled"]
        # Make several requests
        await client.get("/health")
        await client.get("/health")
        r2 = await client.get("/api/status")
        count2 = r2.json()["requests_handled"]
        assert count2 > count1


# ===================================================================
# 17. COMPARE ENDPOINT EDGE CASES
# ===================================================================

class TestCompareEdgeCases:
    """Additional edge cases for the compare endpoint."""

    async def test_duplicate_codes(self, client):
        """Duplicate codes like ATL,ATL should be handled (no crash)."""
        r = await client.get("/api/compare", params={"codes": "ATL,ATL"})
        assert r.status_code == 200

    async def test_mixed_case_codes(self, client):
        """Mixed case codes should be normalized."""
        r = await client.get("/api/compare", params={"codes": "atl,Jfk"})
        assert r.status_code == 200
        codes = {a["code"] for a in r.json()["airports"]}
        assert "ATL" in codes
        assert "JFK" in codes

    async def test_codes_with_spaces(self, client):
        """Spaces in comma-separated codes should be trimmed."""
        r = await client.get("/api/compare", params={"codes": "ATL, JFK, LAX"})
        assert r.status_code == 200
        assert len(r.json()["airports"]) == 3

    async def test_codes_with_trailing_comma(self, client):
        """Trailing comma should not cause errors."""
        r = await client.get("/api/compare", params={"codes": "ATL,JFK,"})
        assert r.status_code == 200
        # Should have exactly 2 valid results
        valid = [a for a in r.json()["airports"] if "error" not in a]
        assert len(valid) == 2

    async def test_all_unknown_codes_400(self, client):
        """All unknown but valid-format codes should still return 200 with errors."""
        r = await client.get("/api/compare", params={"codes": "ZZZ,YYY,XXX"})
        # All have errors but the request itself succeeded
        assert r.status_code == 200
        for ap in r.json()["airports"]:
            assert "error" in ap

    async def test_compare_radius_max_15(self, client):
        """Compare has max radius of 15 (different from buildings' 20)."""
        r = await client.get("/api/compare", params={"codes": "ATL", "radius": 16})
        assert r.status_code == 422  # exceeds max


# ===================================================================
# 18. SECURITY & INJECTION TESTS
# ===================================================================

class TestSecurity:
    """Test security hardening."""

    async def test_sql_injection_in_params(self, client):
        """SQL-like injection in params should not crash."""
        r = await client.get("/api/buildings/ATL", params={
            "radius": "5; DROP TABLE buildings;--"
        })
        assert r.status_code == 422  # Should fail type validation

    async def test_xss_in_airport_code(self, client):
        """XSS attempt in airport code should be rejected."""
        r = await client.get("/api/buildings/<script>alert(1)</script>")
        assert r.status_code in (400, 404, 422)

    async def test_unicode_in_airport_code(self, client):
        """Unicode chars should be rejected by regex."""
        r = await client.get("/api/buildings/ÄTL")
        assert r.status_code in (400, 404, 422)

    async def test_hsts_header(self, client):
        """HSTS should be present."""
        r = await client.get("/health")
        assert "strict-transport-security" in r.headers
        assert "max-age" in r.headers["strict-transport-security"]

    async def test_xss_protection_header(self, client):
        """X-XSS-Protection header should be set."""
        r = await client.get("/health")
        assert r.headers.get("x-xss-protection") == "1; mode=block"

    async def test_csp_header(self, client):
        """Content-Security-Policy should be present."""
        r = await client.get("/health")
        assert "content-security-policy" in r.headers


# ===================================================================
# 19. FINANCIAL LOGIC DEEP TESTS
# ===================================================================

class TestFinancialLogic:
    """Deep tests on financial calculations."""

    async def test_revenue_higher_than_om_for_large_buildings(self, atl_buildings):
        """Revenue should exceed O&M for any building large enough to make money."""
        for b in atl_buildings["buildings"][:20]:
            s = b["solar"]
            if b["area_m2"] > 1000:
                assert s["annual_revenue"] > s["annual_om"], \
                    f"{b['area_m2']}m²: rev ${s['annual_revenue']} <= om ${s['annual_om']}"

    async def test_simple_payback_formula(self, atl_buildings):
        """simple_payback = install_cost / (annual_revenue - annual_om)."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        net_annual = s["annual_revenue"] - s["annual_om"]
        if net_annual > 0:
            expected = s["install_cost"] / net_annual
            assert abs(s["simple_payback_years"] - round(expected, 1)) < 0.2

    async def test_cost_per_watt_consistent(self, atl_buildings):
        """cost_per_watt * capacity_kw * 1000 should equal gross_install_cost."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        expected = s["cost_per_watt"] * s["capacity_kw"] * 1000
        assert abs(s["gross_install_cost"] - round(expected, 0)) < 100

    async def test_higher_elec_price_always_better_npv(self, client):
        """Higher electricity price should always give better NPV."""
        r1 = await client.get("/api/buildings/ATL", params={
            "radius": 3, "min_size": 5000, "elec_price": 0.05})
        r2 = await client.get("/api/buildings/ATL", params={
            "radius": 3, "min_size": 5000, "elec_price": 0.25})
        for b1, b2 in zip(r1.json()["buildings"][:5], r2.json()["buildings"][:5]):
            assert b2["solar"]["npv_25yr"] > b1["solar"]["npv_25yr"]

    async def test_sunniest_state_best_generation(self, client):
        """PHX (Arizona, CF=0.198) should generate more per m² than SEA (Washington, CF=0.140)."""
        r_phx = await client.get("/api/buildings/PHX", params={"radius": 3, "min_size": 5000})
        r_sea = await client.get("/api/buildings/SEA", params={"radius": 3, "min_size": 5000})
        phx_b = r_phx.json()["buildings"][0]["solar"]
        sea_b = r_sea.json()["buildings"][0]["solar"]
        phx_kwh_per_m2 = phx_b["annual_kwh"] / phx_b["usable_area_m2"]
        sea_kwh_per_m2 = sea_b["annual_kwh"] / sea_b["usable_area_m2"]
        assert phx_kwh_per_m2 > sea_kwh_per_m2

    async def test_co2_lifetime_consistent(self, atl_buildings):
        """co2_lifetime should be roughly annual * 25 adjusted for degradation."""
        b = atl_buildings["buildings"][0]
        s = b["solar"]
        # Lifetime generation factor with degradation
        factor = sum((0.995 ** (y - 1)) for y in range(1, 26))
        expected_lifetime_co2 = s["co2_avoided_tons"] * factor
        assert abs(s["co2_avoided_lifetime_tons"] - round(expected_lifetime_co2, 0)) < 5


# ===================================================================
# 20. FULL WORKFLOW / SMOKE TEST
# ===================================================================

class TestFullWorkflow:
    """End-to-end workflow simulation."""

    async def test_complete_analysis_workflow(self, client):
        """Simulate full user journey: list airports → pick one → get buildings → compare."""
        # Step 1: List airports
        r = await client.get("/api/airports")
        assert r.status_code == 200
        airports = r.json()
        assert len(airports) > 0
        first_code = airports[0]["code"]
        second_code = airports[1]["code"]

        # Step 2: Get buildings for first airport
        r = await client.get(f"/api/buildings/{first_code}", params={
            "radius": 5, "min_size": 500,
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["buildings"]) > 0
        assert data["totals"]["capacity_mw"] > 0

        # Step 3: Compare two airports
        r = await client.get("/api/compare", params={
            "codes": f"{first_code},{second_code}",
        })
        assert r.status_code == 200
        assert len(r.json()["airports"]) == 2

        # Step 4: Get aggregate
        r = await client.get("/api/aggregate", params={"min_size": 2000})
        assert r.status_code == 200
        agg = r.json()
        assert agg["totals"]["airport_count"] >= 20

    async def test_api_docs_accessible(self, client):
        """OpenAPI docs should be served."""
        r = await client.get("/api/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        assert "paths" in spec
        assert "/api/buildings/{airport_code}" in spec["paths"]
        assert "/api/compare" in spec["paths"]
        assert "/api/aggregate" in spec["paths"]

    async def test_response_times_reasonable(self, client):
        """Health should respond in < 100ms, buildings in < 10s."""
        import time

        t0 = time.time()
        await client.get("/health")
        health_time = time.time() - t0
        assert health_time < 0.1, f"Health took {health_time:.3f}s"

        t0 = time.time()
        await client.get("/api/buildings/ATL", params={"radius": 5, "min_size": 1000})
        building_time = time.time() - t0
        assert building_time < 10, f"Buildings took {building_time:.3f}s"


# ===================================================================
# 21. GEOGRAPHY & DISTANCE TESTS
# ===================================================================

class TestGeography:
    """Verify geographic accuracy of the system."""

    async def test_building_centroid_matches_geometry(self, atl_buildings):
        """Building lat/lon should be near the centroid of its geometry."""
        for b in atl_buildings["buildings"][:10]:
            geom = b["geometry"]
            if geom["type"] == "Polygon":
                coords = geom["coordinates"][0]
                avg_lon = sum(c[0] for c in coords) / len(coords)
                avg_lat = sum(c[1] for c in coords) / len(coords)
                # Centroid should be near simple average (within ~0.001 degree)
                assert abs(b["lat"] - avg_lat) < 0.005, \
                    f"Lat mismatch: {b['lat']} vs avg {avg_lat}"
                assert abs(b["lon"] - avg_lon) < 0.005, \
                    f"Lon mismatch: {b['lon']} vs avg {avg_lon}"

    async def test_distance_increases_with_radius(self, client):
        """Max distance in results should increase when radius increases."""
        r1 = await client.get("/api/buildings/ATL", params={"radius": 2, "min_size": 500})
        r2 = await client.get("/api/buildings/ATL", params={"radius": 8, "min_size": 500})
        b1 = r1.json()["buildings"]
        b2 = r2.json()["buildings"]
        max_d1 = max(b["distance_km"] for b in b1) if b1 else 0
        max_d2 = max(b["distance_km"] for b in b2) if b2 else 0
        assert max_d2 >= max_d1

    async def test_each_airport_uses_correct_state(self, client, airports):
        """Each airport's solar calcs should use that state's CF."""
        cf_resp = await client.get("/api/capacity-factors")
        cf_map = cf_resp.json()
        for ap in airports[:10]:  # Check first 10
            r = await client.get(f"/api/buildings/{ap['code']}", params={
                "radius": 3, "min_size": 5000
            })
            data = r.json()
            if data["buildings"]:
                actual_cf = data["buildings"][0]["solar"]["capacity_factor"]
                expected_cf = cf_map.get(ap["state"])
                if expected_cf:
                    assert actual_cf == expected_cf, \
                        f"{ap['code']} ({ap['state']}): CF {actual_cf} != expected {expected_cf}"

    async def test_buildings_have_valid_coordinates(self, atl_buildings):
        """All building coordinates should be valid lat/lon."""
        for b in atl_buildings["buildings"]:
            assert -90 <= b["lat"] <= 90, f"Invalid lat: {b['lat']}"
            assert -180 <= b["lon"] <= 180, f"Invalid lon: {b['lon']}"


# ===================================================================
# 22. EMPTY / DEGENERATE DATA SCENARIOS
# ===================================================================

class TestEmptyScenarios:
    """Test behavior when data is sparse or empty."""

    async def test_no_buildings_returns_empty_array(self, client):
        """Very restrictive params should return 200 with empty or small list."""
        r = await client.get("/api/buildings/BOS", params={
            "radius": 1, "min_size": 10000
        })
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["buildings"], list)
        # Totals should be None if no buildings
        if len(data["buildings"]) == 0:
            assert data["totals"] is None

    async def test_compare_mixed_empty_and_full(self, client):
        """Compare with one airport having no buildings and one having many."""
        r = await client.get("/api/compare", params={
            "codes": "ATL,ZZZ", "min_size": 5000
        })
        assert r.status_code == 200
        results = r.json()["airports"]
        atl = next(a for a in results if a["code"] == "ATL")
        zzz = next(a for a in results if a["code"] == "ZZZ")
        assert "totals" in atl
        assert "error" in zzz

    async def test_building_count_monotonic_with_radius(self, client):
        """Larger radius should always have >= building count of smaller radius."""
        counts = []
        for r_val in [1, 3, 5, 10]:
            r = await client.get("/api/buildings/ATL", params={
                "radius": r_val, "min_size": 1000
            })
            counts.append(len(r.json()["buildings"]))
        for i in range(len(counts) - 1):
            assert counts[i + 1] >= counts[i], \
                f"Count decreased: radius {[1,3,5,10][i]}={counts[i]} > radius {[1,3,5,10][i+1]}={counts[i+1]}"

    async def test_building_count_monotonic_with_min_size(self, client):
        """Larger min_size should always have <= building count of smaller min_size."""
        counts = []
        for ms in [200, 500, 1000, 5000]:
            r = await client.get("/api/buildings/ATL", params={
                "radius": 5, "min_size": ms
            })
            counts.append(len(r.json()["buildings"]))
        for i in range(len(counts) - 1):
            assert counts[i + 1] <= counts[i], \
                f"Count increased: min_size {[200,500,1000,5000][i]}={counts[i]} < min_size {[200,500,1000,5000][i+1]}={counts[i+1]}"


# ===================================================================
# 23. OPENAPI SPEC VALIDATION
# ===================================================================

class TestOpenAPISpec:
    """Verify the API is self-documenting correctly."""

    async def test_openapi_lists_all_endpoints(self, client):
        """OpenAPI spec should document every endpoint."""
        r = await client.get("/api/openapi.json")
        spec = r.json()
        paths = spec["paths"]
        expected = ["/health", "/api/health", "/api/status", "/api/ready",
                    "/api/airports", "/api/capacity-factors",
                    "/api/buildings/{airport_code}", "/api/compare", "/api/aggregate"]
        for ep in expected:
            assert ep in paths, f"Missing from OpenAPI spec: {ep}"

    async def test_openapi_version_matches(self, client):
        """OpenAPI spec version should match /api/status version."""
        spec = (await client.get("/api/openapi.json")).json()
        status = (await client.get("/api/status")).json()
        assert spec["info"]["version"] == status["version"]


# ===================================================================
# 24. SCALING & CAPACITY TESTS
# ===================================================================

class TestScaling:
    """Test the system under larger queries."""

    async def test_max_radius_max_min_size_all_airports(self, client, airports):
        """Every airport at max radius still responds (no timeout/crash)."""
        for ap in airports[:5]:  # Top 5 to keep test fast
            r = await client.get(f"/api/buildings/{ap['code']}", params={
                "radius": 20, "min_size": 100
            })
            assert r.status_code == 200
            assert len(r.json()["buildings"]) <= 5000  # MAX_BUILDINGS cap

    async def test_aggregate_response_size_reasonable(self, client):
        """Aggregate response should be JSON-serializable and < 100KB."""
        r = await client.get("/api/aggregate", params={"min_size": 5000})
        assert r.status_code == 200
        size = len(r.content)
        assert size < 100_000, f"Aggregate response too large: {size} bytes"
