import React from 'react';
import { RiskFlag } from '../api/types';

interface RiskRegisterProps {
  risks: RiskFlag[];
}

export const RiskRegister: React.FC<RiskRegisterProps> = ({ risks }) => {
  if (risks.length === 0) {
    return (
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-sm">
        ✅ No critical scale-up risks flagged for this scenario.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {risks.map((risk) => {
        const isCritical = risk.severity === 'critical';
        return (
          <div
            key={risk.id}
            className={`p-4 rounded-lg border text-sm ${
              isCritical
                ? 'bg-rose-50 border-rose-200 text-rose-900'
                : 'bg-amber-50 border-amber-200 text-amber-900'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-base flex items-center gap-2">
                <span>{isCritical ? '🚨' : '⚠️'}</span>
                {risk.title}
              </span>
              <span
                className={`text-xs uppercase font-bold px-2 py-0.5 rounded ${
                  isCritical ? 'bg-rose-200 text-rose-800' : 'bg-amber-200 text-amber-800'
                }`}
              >
                {risk.severity}
              </span>
            </div>
            <p className="mt-2 text-slate-700 leading-relaxed">{risk.description}</p>
            {risk.mitigation_suggestion && (
              <div className="mt-2 text-xs font-medium text-slate-900 bg-white/70 p-2 rounded border border-slate-200">
                💡 <strong>Mitigation:</strong> {risk.mitigation_suggestion}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
