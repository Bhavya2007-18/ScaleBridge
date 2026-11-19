import React from 'react';
import { Vessel } from '../api/types';

interface VesselCompareTableProps {
  sourceVessel: Vessel;
  targetVessel: Vessel;
}

export const VesselCompareTable: React.FC<VesselCompareTableProps> = ({
  sourceVessel,
  targetVessel,
}) => {
  return (
    <div className="overflow-x-auto border border-slate-200 rounded-lg">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 border-b border-slate-200 text-slate-700">
          <tr>
            <th className="p-3 font-semibold">Geometric / Operating Parameter</th>
            <th className="p-3 font-semibold">Source ({sourceVessel.name})</th>
            <th className="p-3 font-semibold">Target ({targetVessel.name})</th>
            <th className="p-3 font-semibold">Scale Ratio</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          <tr>
            <td className="p-3 font-medium text-slate-800">Working Volume (L)</td>
            <td className="p-3">{sourceVessel.working_volume_max_l} L</td>
            <td className="p-3">{targetVessel.working_volume_max_l} L</td>
            <td className="p-3 font-bold text-indigo-600">
              {(targetVessel.working_volume_max_l / (sourceVessel.working_volume_max_l || 1)).toFixed(1)}x
            </td>
          </tr>
          <tr>
            <td className="p-3 font-medium text-slate-800">Scale Category</td>
            <td className="p-3 capitalize">{sourceVessel.scale_category}</td>
            <td className="p-3 capitalize">{targetVessel.scale_category}</td>
            <td className="p-3 text-slate-400">—</td>
          </tr>
          <tr>
            <td className="p-3 font-medium text-slate-800">Impeller Types</td>
            <td className="p-3">{sourceVessel.impeller_types.join(', ')}</td>
            <td className="p-3">{targetVessel.impeller_types.join(', ')}</td>
            <td className="p-3 text-slate-400">—</td>
          </tr>
          <tr>
            <td className="p-3 font-medium text-slate-800">Max Agitation (RPM)</td>
            <td className="p-3">{sourceVessel.max_rpm ?? 'N/A'} RPM</td>
            <td className="p-3">{targetVessel.max_rpm ?? 'N/A'} RPM</td>
            <td className="p-3 text-slate-400">—</td>
          </tr>
          <tr>
            <td className="p-3 font-medium text-slate-800">Max Motor Power (W)</td>
            <td className="p-3">{sourceVessel.max_power_w ?? 'N/A'} W</td>
            <td className="p-3">{targetVessel.max_power_w ?? 'N/A'} W</td>
            <td className="p-3 text-slate-400">—</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};
