import React from 'react';
import { useVessels } from '../api/hooks/useData';

export const Vessels: React.FC = () => {
  const { vessels, loading, error } = useVessels();

  return (
    <div className="space-y-8">
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-mono uppercase tracking-widest text-[#2fe578] mb-3">
          <span className="w-1.5 h-1.5 rounded-full bg-[#2fe578]"></span>
          Hardware Custody Registry
        </div>
        <h1 className="text-3xl font-display font-bold text-white">Bioreactor Equipment Fleet</h1>
        <p className="text-xs text-[#8e9e94] mt-1 font-light">
          Calibrated physical geometries, motor utility ceilings, and aeration sparger profiles across pilot and production suites.
        </p>
      </div>

      {loading && <div className="text-xs font-mono text-[#708076] py-12 text-center">Reading vessel calibration blocks...</div>}
      {error && <div className="text-xs font-mono text-rose-400 py-6 text-center">[Sync Error]: {error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {vessels.map((v) => (
          <div key={v.id} className="p-6 rounded-3xl euronium-glass-card space-y-4">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="px-2.5 py-0.5 rounded-full bg-[#2fe578]/10 border border-[#2fe578]/30 text-[#2fe578] text-[10px] uppercase font-semibold">
                {v.scale_category} NODE
              </span>
              <span className="text-[10px] text-[#708076]">{v.facility || 'Facility #01'}</span>
            </div>

            <div>
              <h3 className="font-display font-bold text-lg text-white">{v.name}</h3>
              <p className="text-xs font-mono text-[#7cf6b1] mt-0.5">
                Volumetric Span: {v.working_volume_min_l}L – {v.working_volume_max_l}L
              </p>
            </div>

            <div className="space-y-2 pt-3 border-t border-white/5 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-white/[0.03]">
                <span className="text-[#8e9e94]">Agitation Speed Ceiling</span>
                <span className="text-white">{v.max_rpm ?? '—'} RPM</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.03]">
                <span className="text-[#8e9e94]">Motor Utility Power</span>
                <span className="text-white">{v.max_power_w ?? '—'} Watts</span>
              </div>
              <div className="flex justify-between py-1 border-b border-white/[0.03]">
                <span className="text-[#8e9e94]">Aeration Envelope</span>
                <span className="text-white">{v.max_gassing_vvm ?? '—'} VVM</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#8e9e94]">Impeller Architecture</span>
                <span className="text-[#d0ded5] text-right truncate max-w-[160px]">{v.impeller_types.join(', ')}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
