'use client';

import { useState, useEffect, useCallback } from 'react';

export interface CustomBuilding {
  id: string;
  geometry: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  area_m2: number;
  lat: number;
  lon: number;
  distance_km: number;
  isCustom: true;
  label?: string;
}

/**
 * Calculate geodesic area of a polygon from LatLng array.
 * Uses the shoelace formula on an equirectangular projection.
 * Good enough for building-scale polygons.
 */
export function calcGeodesicArea(latlngs: { lat: number; lng: number }[]): number {
  if (latlngs.length < 3) return 0;
  // Use the mean latitude for equirectangular projection
  const meanLat = latlngs.reduce((s, p) => s + p.lat, 0) / latlngs.length;
  const cosLat = Math.cos((meanLat * Math.PI) / 180);
  const R = 6371000; // Earth radius in meters

  // Convert to meters relative to first point
  const pts = latlngs.map(p => ({
    x: (p.lng - latlngs[0].lng) * (Math.PI / 180) * R * cosLat,
    y: (p.lat - latlngs[0].lat) * (Math.PI / 180) * R,
  }));

  // Shoelace formula
  let area = 0;
  for (let i = 0; i < pts.length; i++) {
    const j = (i + 1) % pts.length;
    area += pts[i].x * pts[j].y;
    area -= pts[j].x * pts[i].y;
  }
  return Math.abs(area / 2);
}

/**
 * Calculate distance between two lat/lng points in km (Haversine).
 */
export function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Convert an array of {lat, lng} points to a GeoJSON Polygon geometry.
 */
export function latlngsToGeoJSON(latlngs: { lat: number; lng: number }[]): { type: 'Polygon'; coordinates: number[][][] } {
  const ring = latlngs.map(p => [p.lng, p.lat]);
  // Close the ring
  if (ring.length > 0 && (ring[0][0] !== ring[ring.length - 1][0] || ring[0][1] !== ring[ring.length - 1][1])) {
    ring.push([ring[0][0], ring[0][1]]);
  }
  return { type: 'Polygon', coordinates: [ring] };
}

/**
 * Calculate centroid of lat/lng points.
 */
export function centroid(latlngs: { lat: number; lng: number }[]): { lat: number; lng: number } {
  const lat = latlngs.reduce((s, p) => s + p.lat, 0) / latlngs.length;
  const lng = latlngs.reduce((s, p) => s + p.lng, 0) / latlngs.length;
  return { lat, lng };
}

/**
 * Hook to manage user-drawn custom buildings per airport, persisted in localStorage.
 */
export function useCustomBuildings(airportCode: string, airportCenter: [number, number]) {
  const [buildings, setBuildings] = useState<CustomBuilding[]>([]);

  // Load from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(`custom_buildings_${airportCode}`);
      if (stored) {
        setBuildings(JSON.parse(stored));
      } else {
        setBuildings([]);
      }
    } catch {
      setBuildings([]);
    }
  }, [airportCode]);

  const persist = useCallback((items: CustomBuilding[]) => {
    try {
      if (items.length > 0) {
        localStorage.setItem(`custom_buildings_${airportCode}`, JSON.stringify(items));
      } else {
        localStorage.removeItem(`custom_buildings_${airportCode}`);
      }
    } catch {
      // localStorage full — fail silently
    }
  }, [airportCode]);

  /**
   * Add a custom building from drawn polygon points.
   */
  const addBuilding = useCallback((latlngs: { lat: number; lng: number }[], label?: string): CustomBuilding | null => {
    if (latlngs.length < 3) return null;

    const area = calcGeodesicArea(latlngs);
    if (area < 1) return null; // Too small

    const center = centroid(latlngs);
    const dist = haversineKm(airportCenter[0], airportCenter[1], center.lat, center.lng);

    const building: CustomBuilding = {
      id: `custom_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      geometry: latlngsToGeoJSON(latlngs),
      area_m2: Math.round(area),
      lat: Math.round(center.lat * 10000) / 10000,
      lon: Math.round(center.lng * 10000) / 10000,
      distance_km: Math.round(dist * 100) / 100,
      isCustom: true,
      label,
    };

    setBuildings(prev => {
      const next = [...prev, building];
      persist(next);
      return next;
    });

    return building;
  }, [airportCenter, persist]);

  const removeBuilding = useCallback((id: string) => {
    setBuildings(prev => {
      const next = prev.filter(b => b.id !== id);
      persist(next);
      return next;
    });
  }, [persist]);

  const removeAll = useCallback(() => {
    setBuildings([]);
    persist([]);
  }, [persist]);

  return {
    customBuildings: buildings,
    customCount: buildings.length,
    addBuilding,
    removeBuilding,
    removeAll,
  };
}
