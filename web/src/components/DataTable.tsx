'use client';

import { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronRight, MapPin, CheckSquare, Square, MinusSquare } from 'lucide-react';

interface Building {
  area_m2: number;
  distance_km: number;
  lat: number;
  lon: number;
  isCustom?: boolean;
  id?: string;
  solar?: {
    capacity_kw: number;
    annual_mwh: number;
    annual_revenue: number;
    payback_years: number;
    co2_avoided_tons?: number;
  };
}

interface DataTableProps {
  buildings: Building[];
  state: string;
  onRowClick?: (building: Building) => void;
  onLocate?: (building: Building) => void;
  selectedKeys?: Set<string>;
  onToggleSelect?: (building: Building) => void;
  onSelectPage?: (buildings: Building[], selected: boolean) => void;
}

type SortField = 'area_m2' | 'distance_km' | 'capacity_kw' | 'annual_mwh' | 'annual_revenue' | 'payback_years';
type SortDirection = 'asc' | 'desc';

const PAGE_SIZE = 25;

export function DataTable({ buildings, state, onRowClick, onLocate, selectedKeys, onToggleSelect, onSelectPage }: DataTableProps) {
  const [sortField, setSortField] = useState<SortField>('area_m2');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [page, setPage] = useState(0);

  const sortedBuildings = useMemo(() => {
    return [...buildings].sort((a, b) => {
      let aVal: number, bVal: number;
      switch (sortField) {
        case 'area_m2': aVal = a.area_m2; bVal = b.area_m2; break;
        case 'distance_km': aVal = a.distance_km; bVal = b.distance_km; break;
        case 'capacity_kw': aVal = a.solar?.capacity_kw || 0; bVal = b.solar?.capacity_kw || 0; break;
        case 'annual_mwh': aVal = a.solar?.annual_mwh || 0; bVal = b.solar?.annual_mwh || 0; break;
        case 'annual_revenue': aVal = a.solar?.annual_revenue || 0; bVal = b.solar?.annual_revenue || 0; break;
        case 'payback_years': aVal = a.solar?.payback_years || 999; bVal = b.solar?.payback_years || 999; break;
        default: aVal = a.area_m2; bVal = b.area_m2;
      }
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });
  }, [buildings, sortField, sortDirection]);

  const totalPages = Math.ceil(sortedBuildings.length / PAGE_SIZE);
  const pagedBuildings = sortedBuildings.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
    setPage(0);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (field !== sortField) return <ArrowUpDown className="w-4 h-4 text-gray-400" />;
    return sortDirection === 'asc'
      ? <ArrowUp className="w-4 h-4 text-primary-600" />
      : <ArrowDown className="w-4 h-4 text-primary-600" />;
  };

  const bKey = (b: Building) => `${b.lat}_${b.lon}_${b.area_m2}`;
  const hasSelection = selectedKeys && onToggleSelect;
  const pageAllSelected = hasSelection ? pagedBuildings.length > 0 && pagedBuildings.every(b => selectedKeys.has(bKey(b))) : false;
  const pageSomeSelected = hasSelection ? pagedBuildings.some(b => selectedKeys.has(bKey(b))) && !pageAllSelected : false;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            {hasSelection && (
              <th className="py-3 px-2 w-10">
                <button
                  onClick={() => onSelectPage?.(pagedBuildings, !pageAllSelected)}
                  className="p-0.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                  title={pageAllSelected ? 'Deselect page' : 'Select page'}
                >
                  {pageAllSelected ? <CheckSquare className="w-4 h-4 text-primary-600" /> : pageSomeSelected ? <MinusSquare className="w-4 h-4 text-primary-600" /> : <Square className="w-4 h-4" />}
                </button>
              </th>
            )}
            <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400 w-16">Rank</th>
            {([
              ['area_m2', 'Roof Area (m²)'],
              ['distance_km', 'Distance (km)'],
              ['capacity_kw', 'Capacity (kW)'],
              ['annual_mwh', 'Annual (MWh)'],
              ['annual_revenue', 'Revenue ($/yr)'],
              ['payback_years', 'Payback (yr)'],
            ] as [SortField, string][]).map(([field, label]) => (
              <th key={field} className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">
                <button onClick={() => handleSort(field)} className="inline-flex items-center gap-1 hover:text-gray-700 dark:hover:text-gray-200">
                  {label} <SortIcon field={field} />
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {pagedBuildings.map((b, i) => {
            const isChecked = hasSelection && selectedKeys.has(bKey(b));
            return (
            <tr
              key={page * PAGE_SIZE + i}
              className={`border-b border-gray-100 dark:border-gray-700 transition-colors ${
                isChecked ? 'bg-blue-50 dark:bg-blue-900/20 cursor-pointer' :
                'cursor-pointer hover:bg-primary-50 dark:hover:bg-primary-900/20'
              }`}
              onClick={() => onRowClick?.(b)}
            >
              {hasSelection && (
                <td className="py-3 px-2 text-center">
                  <button
                    onClick={(e) => { e.stopPropagation(); onToggleSelect(b); }}
                    className="p-0.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                  >
                    {isChecked ? <CheckSquare className="w-4 h-4 text-blue-500" /> : <Square className="w-4 h-4" />}
                  </button>
                </td>
              )}
              <td className="py-3 px-4 text-gray-400 font-medium">#{page * PAGE_SIZE + i + 1}</td>
              <td className="py-3 px-4 text-right font-medium text-gray-900 dark:text-gray-100 tabular-nums">{b.area_m2.toLocaleString()}</td>
              <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400 tabular-nums">{b.distance_km.toFixed(2)}</td>
              <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400 tabular-nums">{b.solar?.capacity_kw.toLocaleString() || '-'}</td>
              <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400 tabular-nums">{b.solar?.annual_mwh.toLocaleString() || '-'}</td>
              <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400 tabular-nums">${b.solar?.annual_revenue.toLocaleString() || '-'}</td>
              <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400 tabular-nums">{b.solar?.payback_years.toFixed(1) || '-'}</td>
              <td className="py-2 px-2 text-center">
                {onLocate && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onLocate(b); }}
                    className="p-1.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-md transition-colors"
                    title="Locate on map"
                    aria-label="Locate on map"
                  >
                    <MapPin className="w-3.5 h-3.5" />
                  </button>
                )}
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-3 px-2">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, sortedBuildings.length)} of {sortedBuildings.length} buildings
        </span>
        {totalPages > 1 && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Previous page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              const pageNum = totalPages <= 7 ? i : (page < 4 ? i : page > totalPages - 4 ? totalPages - 7 + i : page - 3 + i);
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-8 h-8 text-xs rounded-md ${
                    page === pageNum
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  {pageNum + 1}
                </button>
              );
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page === totalPages - 1}
              className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Next page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
