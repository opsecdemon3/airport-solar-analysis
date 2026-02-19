'use client';

import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: number;
  unit?: string;
  prefix?: string;
  format?: 'number' | 'decimal';
  decimals?: number;
  loading?: boolean;
}

export function MetricCard({
  icon: Icon,
  label,
  value,
  unit = '',
  prefix = '',
  format = 'number',
  decimals = 0,
  loading = false,
}: MetricCardProps) {
  const formattedValue =
    format === 'number'
      ? value.toLocaleString()
      : value.toFixed(decimals);

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-lg skeleton dark:!bg-gray-700" />
          <div className="h-4 w-20 rounded skeleton dark:!bg-gray-700" />
        </div>
        <div className="h-8 w-32 rounded skeleton dark:!bg-gray-700" />
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700 card-hover">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-primary-50 dark:bg-primary-900/30 rounded-lg">
          <Icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {prefix}
        {formattedValue}
        {unit && <span className="text-lg font-normal text-gray-500 dark:text-gray-400 ml-1">{unit}</span>}
      </div>
    </div>
  );
}
