import React from 'react';
import { RiskFlag } from '../api/types';

interface RiskRegisterProps {
  risks: RiskFlag[];
}

export const RiskRegister: React.FC<RiskRegisterProps> = ({ risks }) => {
  if (risks.length === 0) {
    return (
      <div className="p-6 bg-[#0f1712]/70 border border-[#2fe578]/20 rounded-2xl text-[#7cf6b1] text-sm font-mono flex items-center gap-3">
        <span className="w-2.5 h-2.5 rounded-full bg-[#2fe578]"></span>
        <span>Verified: No kinetic or hydrodynamic anomalies detected across custody nodes.</span>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {risks.map((risk) => {
        const isCritical = risk.severity === 'critical';
        return (
          <div
            key={risk.id}
            className={`p-5 rounded-2xl border transition duration-300 relative overflow-hidden ${
              isCritical
                ? 'bg-rose-950/20 border-rose-500/30 text-rose-200 hover:border-rose-500/50'
                : 'bg-[#121c16]/70 border-amber-500/25 text-amber-100 hover:border-amber-400/40'
            }`}
          >
            <div className="flex items-center justify-between font-mono text-[11px] mb-3">
              <span className="uppercase tracking-widest text-[#8e9e94] flex items-center gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${isCritical ? 'bg-rose-400' : 'bg-amber-400'}`}></span>
                LAYER: {risk.category}
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${
                  isCritical ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                }`}
              >
                {risk.severity} FLAG
              </span>
            </div>
            <h4 className="font-display font-semibold text-base text-white tracking-wide">{risk.title}</h4>
            <p className="mt-2 text-xs text-[#a3b3a9] leading-relaxed font-light">{risk.description}</p>
            {risk.mitigation_suggestion && (
              <div className="mt-4 pt-3 border-t border-white/5 flex items-start gap-2 text-xs text-[#d0ded5]">
                <span className="text-[#2fe578] font-mono text-[10px] uppercase tracking-wider shrink-0 mt-0.5">Custody Directive:</span>
                <span className="font-light">{risk.mitigation_suggestion}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
