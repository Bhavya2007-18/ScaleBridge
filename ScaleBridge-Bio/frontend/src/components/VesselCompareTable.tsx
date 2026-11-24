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
    <div className="overflow-hidden border border-white/10 rounded-2xl bg-[#0f1612]/70 backdrop-blur-md">
      <div className="p-4 border-b border-white/5 flex items-center justify-between text-xs font-mono text-[#8e9e94]">
        <span>VESSEL GEOMETRY MATRIX (CUSTODY NODES)</span>
        <span className="text-[#2fe578]">EXPANSION MULTIPLIER: {(targetVessel.working_volume_max_l / (sourceVessel.working_volume_max_l || 1)).toFixed(1)}X</span>
      </div>
      <table className="w-full text-left text-xs font-mono">
        <thead className="bg-white/[0.02] text-[#8e9e94] border-b border-white/5 uppercase tracking-wider text-[10px]">
          <tr>
            <th className="p-4 font-normal">Physical Metric</th>
            <th className="p-4 font-normal">Origin Node ({sourceVessel.name})</th>
            <th className="p-4 font-normal">Destination Node ({targetVessel.name})</th>
            <th className="p-4 font-normal">Transformation Factor</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5 text-[#d0ded5]">
          <tr className="hover:bg-white/[0.01] transition">
            <td className="p-4 text-[#e3e9e5] font-sans font-medium">Working Volume</td>
            <td className="p-4 font-mono">{sourceVessel.working_volume_max_l} Liters</td>
            <td className="p-4 font-mono text-[#2fe578] font-bold">{targetVessel.working_volume_max_l} Liters</td>
            <td className="p-4 text-[#7cf6b1]">{(targetVessel.working_volume_max_l / (sourceVessel.working_volume_max_l || 1)).toFixed(1)}x Volumetric Shift</td>
          </tr>
          <tr className="hover:bg-white/[0.01] transition">
            <td className="p-4 text-[#e3e9e5] font-sans font-medium">Classification Tier</td>
            <td className="p-4 uppercase">{sourceVessel.scale_category} (Bench)</td>
            <td className="p-4 uppercase text-[#2fe578]">{targetVessel.scale_category} (Plant)</td>
            <td className="p-4 text-white/40">Verified Step</td>
          </tr>
          <tr className="hover:bg-white/[0.01] transition">
            <td className="p-4 text-[#e3e9e5] font-sans font-medium">Impeller Architecture</td>
            <td className="p-4 font-sans text-xs">{sourceVessel.impeller_types.join(', ')}</td>
            <td className="p-4 font-sans text-xs">{targetVessel.impeller_types.join(', ')}</td>
            <td className="p-4 text-white/40">Geometric Non-similarity flagged</td>
          </tr>
          <tr className="hover:bg-white/[0.01] transition">
            <td className="p-4 text-[#e3e9e5] font-sans font-medium">Max Kinetic Drive (RPM)</td>
            <td className="p-4 font-mono">{sourceVessel.max_rpm ?? '—'} RPM</td>
            <td className="p-4 font-mono">{targetVessel.max_rpm ?? '—'} RPM</td>
            <td className="p-4 text-white/40">Drive Envelope OK</td>
          </tr>
          <tr className="hover:bg-white/[0.01] transition">
            <td className="p-4 text-[#e3e9e5] font-sans font-medium">Motor Power Rating</td>
            <td className="p-4 font-mono">{sourceVessel.max_power_w ?? '—'} W</td>
            <td className="p-4 font-mono text-[#7cf6b1]">{targetVessel.max_power_w ?? '—'} W</td>
            <td className="p-4 text-[#7cf6b1]">Sufficient Utility Headroom</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};
