'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * Generate a unique key for a building based on its coordinates and area.
 * This is deterministic — same building always gets the same key.
 */
export function buildingKey(building: { lat: number; lon: number; area_m2: number }): string {
  return `${building.lat}_${building.lon}_${building.area_m2}`;
}

/**
 * Hook to manage hidden (excluded) buildings per airport, persisted in localStorage.
 */
export function useHiddenBuildings(airportCode: string) {
  const [hiddenKeys, setHiddenKeys] = useState<Set<string>>(new Set());

  // Load from localStorage when airport changes
  useEffect(() => {
    try {
      const stored = localStorage.getItem(`hidden_buildings_${airportCode}`);
      if (stored) {
        setHiddenKeys(new Set(JSON.parse(stored)));
      } else {
        setHiddenKeys(new Set());
      }
    } catch {
      setHiddenKeys(new Set());
    }
  }, [airportCode]);

  // Save to localStorage whenever hiddenKeys changes
  const persist = useCallback((keys: Set<string>) => {
    try {
      if (keys.size > 0) {
        localStorage.setItem(`hidden_buildings_${airportCode}`, JSON.stringify(Array.from(keys)));
      } else {
        localStorage.removeItem(`hidden_buildings_${airportCode}`);
      }
    } catch {
      // localStorage full or unavailable — fail silently
    }
  }, [airportCode]);

  const hideBuilding = useCallback((building: { lat: number; lon: number; area_m2: number }) => {
    setHiddenKeys(prev => {
      const next = new Set(prev);
      next.add(buildingKey(building));
      persist(next);
      return next;
    });
  }, [persist]);

  const hideMultiple = useCallback((buildings: { lat: number; lon: number; area_m2: number }[]) => {
    setHiddenKeys(prev => {
      const next = new Set(prev);
      buildings.forEach(b => next.add(buildingKey(b)));
      persist(next);
      return next;
    });
  }, [persist]);

  const restoreBuilding = useCallback((key: string) => {
    setHiddenKeys(prev => {
      const next = new Set(prev);
      next.delete(key);
      persist(next);
      return next;
    });
  }, [persist]);

  const restoreAll = useCallback(() => {
    setHiddenKeys(new Set());
    persist(new Set());
  }, [persist]);

  const isHidden = useCallback((building: { lat: number; lon: number; area_m2: number }) => {
    return hiddenKeys.has(buildingKey(building));
  }, [hiddenKeys]);

  return {
    hiddenKeys,
    hiddenCount: hiddenKeys.size,
    hideBuilding,
    hideMultiple,
    restoreBuilding,
    restoreAll,
    isHidden,
  };
}

/**
 * Recalculate aggregate totals from a filtered list of buildings.
 * Used when buildings are excluded so metrics stay accurate.
 */
export function recalcTotals(buildings: any[], originalTotals: any): any {
  if (!buildings.length || !originalTotals) return originalTotals;

  const totalArea = buildings.reduce((s, b) => s + (b.area_m2 || 0), 0);
  const capacityKw = buildings.reduce((s, b) => s + (b.solar?.capacity_kw || 0), 0);
  const annualMwh = buildings.reduce((s, b) => s + (b.solar?.annual_mwh || 0), 0);
  const annualRevenue = buildings.reduce((s, b) => s + (b.solar?.annual_revenue || 0), 0);
  const grossCost = buildings.reduce((s, b) => s + (b.solar?.gross_install_cost || 0), 0);
  const itcSavings = buildings.reduce((s, b) => s + (b.solar?.itc_savings || 0), 0);
  const installCost = buildings.reduce((s, b) => s + (b.solar?.install_cost || 0), 0);
  const annualOm = buildings.reduce((s, b) => s + (b.solar?.annual_om || 0), 0);
  const npv = buildings.reduce((s, b) => s + (b.solar?.npv_25yr || 0), 0);
  const co2 = buildings.reduce((s, b) => s + (b.solar?.co2_avoided_tons || 0), 0);
  const co2Lifetime = buildings.reduce((s, b) => s + (b.solar?.co2_avoided_lifetime_tons || 0), 0);
  const homes = buildings.reduce((s, b) => s + (b.solar?.homes_powered || 0), 0);
  const lifetimeMwh = buildings.reduce((s, b) => s + (b.solar?.lifetime_mwh || 0), 0);

  const netAnnual = annualRevenue - annualOm;
  const payback = netAnnual > 0 ? installCost / netAnnual : 999;

  return {
    ...originalTotals,
    building_count: buildings.length,
    total_roof_area_m2: Math.round(totalArea),
    capacity_kw: Math.round(capacityKw * 10) / 10,
    capacity_mw: Math.round(capacityKw / 100) / 10,
    annual_mwh: Math.round(annualMwh * 10) / 10,
    annual_revenue: Math.round(annualRevenue),
    gross_install_cost: Math.round(grossCost),
    itc_savings: Math.round(itcSavings),
    install_cost: Math.round(installCost),
    annual_om: Math.round(annualOm),
    payback_years: Math.round(payback * 10) / 10,
    npv_25yr: Math.round(npv),
    co2_avoided_tons: Math.round(co2 * 10) / 10,
    co2_avoided_lifetime_tons: Math.round(co2Lifetime),
    homes_powered: Math.round(homes),
    lifetime_mwh: Math.round(lifetimeMwh),
  };
}
