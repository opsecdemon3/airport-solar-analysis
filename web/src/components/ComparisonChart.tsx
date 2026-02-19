'use client';

import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Airport {
  code: string;
  airport?: { name: string; state: string };
  totals?: {
    annual_mwh: number;
    capacity_mw: number;
    annual_revenue: number;
    payback_years: number;
    co2_avoided_tons: number;
    npv_25yr: number;
  };
  error?: string;
}

interface ComparisonChartProps {
  airports: Airport[];
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#06b6d4', '#84cc16'];

type Metric = 'energy' | 'capacity' | 'revenue' | 'payback' | 'co2' | 'npv';

const METRICS: { key: Metric; label: string; unit: string; format: (v: number) => string }[] = [
  { key: 'energy', label: 'Annual Energy', unit: 'MWh/yr', format: (v) => `${v.toLocaleString()} MWh` },
  { key: 'capacity', label: 'Peak Capacity', unit: 'MW', format: (v) => `${v.toFixed(1)} MW` },
  { key: 'revenue', label: 'Annual Revenue', unit: '$/yr', format: (v) => `$${(v / 1000).toFixed(0)}k` },
  { key: 'payback', label: 'Payback Period', unit: 'years', format: (v) => `${v.toFixed(1)} yr` },
  { key: 'co2', label: 'CO₂ Avoided', unit: 't/yr', format: (v) => `${v.toLocaleString()} t` },
  { key: 'npv', label: '25-Year NPV', unit: '$', format: (v) => `$${(v / 1e6).toFixed(2)}M` },
];

export function ComparisonChart({ airports }: ComparisonChartProps) {
  const [activeMetric, setActiveMetric] = useState<Metric>('energy');
  const validAirports = airports.filter((a) => a.totals && !a.error);

  if (validAirports.length === 0) {
    return <div className="text-gray-500 dark:text-gray-400 text-center py-8">No data available for comparison</div>;
  }

  const metricConfig = METRICS.find((m) => m.key === activeMetric)!;

  const getValue = (a: Airport): number => {
    const t = a.totals!;
    switch (activeMetric) {
      case 'energy': return t.annual_mwh || 0;
      case 'capacity': return t.capacity_mw || 0;
      case 'revenue': return t.annual_revenue || 0;
      case 'payback': return t.payback_years || 0;
      case 'co2': return t.co2_avoided_tons || 0;
      case 'npv': return t.npv_25yr || 0;
    }
  };

  const chartData = validAirports.map((a, i) => ({
    name: a.code,
    value: getValue(a),
    color: COLORS[i % COLORS.length],
  }));

  const formatYAxis = (value: number) => {
    if (activeMetric === 'revenue' || activeMetric === 'npv') return `$${(value / 1e6).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
    return `${value}`;
  };

  return (
    <div>
      {/* Metric toggle tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        {METRICS.map((m) => (
          <button
            key={m.key}
            onClick={() => setActiveMetric(m.key)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
              activeMetric === m.key
                ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
            <YAxis
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickFormatter={formatYAxis}
              label={{ value: metricConfig.unit, angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              }}
              formatter={(value: number) => [metricConfig.format(value), metricConfig.label]}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
