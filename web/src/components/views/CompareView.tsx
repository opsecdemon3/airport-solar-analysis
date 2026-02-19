'use client';

import { ComparisonChart } from '@/components/ComparisonChart';

interface CompareViewProps {
  data: any;
}

export function CompareView({ data }: CompareViewProps) {
  if (!data?.airports || data.airports.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
        <p className="text-gray-500 dark:text-gray-400 text-lg">
          Select airports above to compare their solar potential
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">Airport Comparison</h2>
      <ComparisonChart airports={data.airports} />
      <div className="overflow-x-auto mt-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Airport</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">State</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Buildings</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Capacity (MW)</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Energy (MWh)</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Revenue ($M/yr)</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">Payback (yr)</th>
              <th className="text-right py-3 px-4 font-medium text-gray-500 dark:text-gray-400">CO₂ (t/yr)</th>
            </tr>
          </thead>
          <tbody>
            {data.airports.map((a: any) => (
              <tr key={a.code} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                  {a.code} - {a.airport?.name || 'N/A'}
                </td>
                <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{a.airport?.state || '-'}</td>
                <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                  {a.totals?.building_count?.toLocaleString() || '-'}
                </td>
                <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                  {a.totals?.capacity_mw?.toFixed(1) || '-'}
                </td>
                <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                  {a.totals?.annual_mwh?.toLocaleString() || '-'}
                </td>
                <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                  ${((a.totals?.annual_revenue || 0) / 1e6).toFixed(1)}
                </td>
                <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                  {a.totals?.payback_years || '-'}
                </td>
                <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                  {a.totals?.co2_avoided_tons?.toLocaleString() || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
