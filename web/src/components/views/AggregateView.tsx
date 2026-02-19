'use client';

import { Home, Leaf, Zap, DollarSign } from 'lucide-react';

interface AggregateViewProps {
  data: any;
}

export function AggregateView({ data }: AggregateViewProps) {
  if (!data) return null;

  return (
    <>
      {/* National Hero */}
      {data.totals && (
        <div className="bg-gradient-to-br from-primary-600 to-purple-600 rounded-2xl p-8 mb-6 text-white text-center">
          <div className="text-5xl sm:text-6xl font-bold mb-2">
            {data.totals.annual_mwh.toLocaleString()} MWh
          </div>
          <div className="text-lg opacity-90 mb-4">
            Total Annual Energy from All {data.totals.airport_count} Airports
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm opacity-80">
            <span className="flex items-center gap-1">
              <Zap className="w-4 h-4" />{data.totals.capacity_mw.toFixed(1)} MW capacity
            </span>
            <span className="flex items-center gap-1">
              <DollarSign className="w-4 h-4" />${(data.totals.annual_revenue / 1e6).toFixed(0)}M annual revenue
            </span>
            <span className="flex items-center gap-1">
              <Home className="w-4 h-4" />{data.totals.homes_powered?.toLocaleString()} homes powered
            </span>
            <span className="flex items-center gap-1">
              <Leaf className="w-4 h-4" />{data.totals.co2_avoided_tons?.toLocaleString()} tons CO₂/yr avoided
            </span>
          </div>
        </div>
      )}

      {/* Rankings Table */}
      {data.airports && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">Airport Rankings by Solar Potential</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Rank</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Airport</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">State</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Buildings</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Energy (MWh)</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Capacity (MW)</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Revenue ($M)</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">CO₂ (t/yr)</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Payback (yr)</th>
                </tr>
              </thead>
              <tbody>
                {data.airports.map((a: any, i: number) => (
                  <tr key={a.code} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="py-3 px-4 font-medium text-gray-400">#{i + 1}</td>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">{a.code} - {a.name}</td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400">{a.state}</td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{a.buildings?.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right font-medium text-gray-900 dark:text-gray-100">{a.annual_mwh?.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{a.capacity_mw?.toFixed(1)}</td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">${((a.annual_revenue || 0) / 1e6).toFixed(2)}</td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{a.co2_avoided_tons?.toLocaleString() || '-'}</td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{a.payback_years || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
