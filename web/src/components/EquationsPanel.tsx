'use client';

import { useMemo } from 'react';

interface EquationsPanelProps {
  usablePct: number;
  panelEff: number;
  elecPrice: number;
  capacityFactor: number;
  costPerWatt?: number;
  itcRate?: number;
}

export function EquationsPanel({ usablePct, panelEff, elecPrice, capacityFactor, costPerWatt = 1.40, itcRate = 0.30 }: EquationsPanelProps) {
  // Example calculation for a 10,000 m² building
  const example = useMemo(() => {
    const area = 10000;
    const usable = area * (usablePct / 100);
    const capacity = usable * panelEff / 1000;
    const energy = capacity * 8760 * capacityFactor;
    const revenue = energy * elecPrice;
    const grossCost = capacity * 1000 * costPerWatt;
    const itcCredit = grossCost * itcRate;
    const netCost = grossCost - itcCredit;
    const payback = netCost / revenue;
    
    return { area, usable, capacity, energy, revenue, grossCost, itcCredit, netCost, payback };
  }, [usablePct, panelEff, elecPrice, capacityFactor, costPerWatt, itcRate]);

  return (
    <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
      <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">📐 How the Math Works</h3>
        
        <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
          <div>
            <span className="font-medium text-gray-900 dark:text-gray-100">Step 1: Usable Area</span>
            <div className="ml-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
              Usable Area = Total Roof Area × {usablePct}%
            </div>
          </div>
          
          <div>
            <span className="font-medium text-gray-900 dark:text-gray-100">Step 2: Peak Capacity (kW)</span>
            <div className="ml-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
              Capacity = Usable Area × {panelEff} W/m² ÷ 1000
            </div>
          </div>
          
          <div>
            <span className="font-medium text-gray-900 dark:text-gray-100">Step 3: Annual Energy (kWh)</span>
            <div className="ml-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
              Energy = Capacity × 8,760 hours × {(capacityFactor * 100).toFixed(1)}% capacity factor
            </div>
            <div className="ml-4 text-gray-500 dark:text-gray-500 font-mono text-xs">
              (CF includes ~14% system losses: inverter, soiling, wiring, mismatch)
            </div>
          </div>
          
          <div>
            <span className="font-medium text-gray-900 dark:text-gray-100">Step 4: Annual Revenue</span>
            <div className="ml-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
              Revenue = Annual Energy × ${elecPrice.toFixed(2)}/kWh
            </div>
          </div>
          
          <div>
            <span className="font-medium text-gray-900 dark:text-gray-100">Step 5: Installation Cost & ITC</span>
            <div className="ml-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
              Gross Cost = Capacity × ${costPerWatt.toFixed(2)}/W (commercial rooftop, 2025)
            </div>
            <div className="ml-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
              ITC Credit = Gross Cost × {(itcRate * 100).toFixed(0)}% (federal investment tax credit)
            </div>
            <div className="ml-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
              Payback = (Gross Cost − ITC Credit) ÷ Annual Revenue
            </div>
          </div>
        </div>

        {/* Live Example */}
        <div className="mt-4 bg-white dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
            Example — 10,000 m² building (CF={`${(capacityFactor * 100).toFixed(1)}%`})
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 px-2 font-medium text-gray-500 dark:text-gray-400">Step</th>
                  <th className="text-left py-2 px-2 font-medium text-gray-500 dark:text-gray-400">Calculation</th>
                  <th className="text-right py-2 px-2 font-medium text-gray-500 dark:text-gray-400">Result</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">Usable Area</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">10,000 × {usablePct}%</td>
                  <td className="py-2 px-2 text-right font-semibold text-gray-900 dark:text-gray-100">{example.usable.toLocaleString()} m²</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">Capacity</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">{example.usable.toLocaleString()} × {panelEff} ÷ 1000</td>
                  <td className="py-2 px-2 text-right font-semibold text-gray-900 dark:text-gray-100">{example.capacity.toLocaleString()} kW</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">Annual Energy</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">{example.capacity.toLocaleString()} × 8,760 × {(capacityFactor * 100).toFixed(1)}%</td>
                  <td className="py-2 px-2 text-right font-semibold text-gray-900 dark:text-gray-100">{Math.round(example.energy).toLocaleString()} kWh</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">Revenue</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">{Math.round(example.energy).toLocaleString()} × ${elecPrice.toFixed(2)}</td>
                  <td className="py-2 px-2 text-right font-semibold text-gray-900 dark:text-gray-100">${Math.round(example.revenue).toLocaleString()}/yr</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">Gross Cost</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">{example.capacity.toLocaleString()} × ${(costPerWatt * 1000).toLocaleString()}/kW</td>
                  <td className="py-2 px-2 text-right font-semibold text-gray-900 dark:text-gray-100">${Math.round(example.grossCost).toLocaleString()}</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">ITC Credit ({(itcRate * 100).toFixed(0)}%)</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">${Math.round(example.grossCost).toLocaleString()} × {(itcRate * 100).toFixed(0)}%</td>
                  <td className="py-2 px-2 text-right font-semibold text-solar-green">−${Math.round(example.itcCredit).toLocaleString()}</td>
                </tr>
                <tr className="border-b border-gray-100 dark:border-gray-700">
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">Net Cost</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">${Math.round(example.grossCost).toLocaleString()} − ${Math.round(example.itcCredit).toLocaleString()}</td>
                  <td className="py-2 px-2 text-right font-semibold text-gray-900 dark:text-gray-100">${Math.round(example.netCost).toLocaleString()}</td>
                </tr>
                <tr>
                  <td className="py-2 px-2 text-gray-700 dark:text-gray-300">Payback</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400 font-mono">${Math.round(example.netCost).toLocaleString()} ÷ ${Math.round(example.revenue).toLocaleString()}</td>
                  <td className="py-2 px-2 text-right font-semibold text-solar-green">{example.payback.toFixed(1)} years</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-gray-500 dark:text-gray-400 italic">
            Capacity factors from NREL PVWatts. Install costs per SEIA/Wood Mackenzie 2025.
            Move the sliders above to see how each parameter changes the result.
          </p>
        </div>
      </div>
    </div>
  );
}
