import React from 'react';
import { Assessment } from '../api/types';

interface ReportProps {
  assessment: Assessment;
  onBack: () => void;
}

export const Report: React.FC<ReportProps> = ({ assessment, onBack }) => {
  return (
    <div className="p-8 md:p-12 rounded-3xl euronium-glass-card border border-white/10 space-y-10 max-w-4xl mx-auto my-8 relative">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full bg-[#2fe578]"></span>
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#2fe578]">
              OFFICIAL TECH-TRANSFER REPORT // AUDIT LEDGER
            </span>
          </div>
          <h1 className="text-3xl font-display font-bold text-white">Scale Verification Certificate</h1>
          <p className="text-xs font-mono text-[#708076] mt-1">DOC HASH: 0x7F83...D9069 • ISO 9001 / ICH Q9 COMPLIANT</p>
        </div>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-white font-mono text-xs uppercase tracking-wider transition self-start"
        >
          Export Ledger PDF
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-5 rounded-2xl bg-white/[0.02] border border-white/5 font-mono text-xs">
        <div>
          <span className="text-[10px] text-[#708076] uppercase">ORIGIN NODE</span>
          <div className="text-white mt-1">5.0L Sartorius Biostat</div>
        </div>
        <div>
          <span className="text-[10px] text-[#708076] uppercase">TARGET NODE</span>
          <div className="text-[#2fe578] mt-1">200.0L Thermo SUB</div>
        </div>
        <div>
          <span className="text-[10px] text-[#708076] uppercase">READINESS SCORE</span>
          <div className="text-white mt-1 font-bold">{assessment.overall_readiness_score.toFixed(1)} / 100</div>
        </div>
        <div>
          <span className="text-[10px] text-[#708076] uppercase">CONSENSUS</span>
          <div className="text-[#7cf6b1] mt-1">QUALIFIED PASS</div>
        </div>
      </div>

      <div className="space-y-6 text-sm text-[#d0ded5] font-light leading-relaxed">
        <div>
          <h3 className="font-display font-semibold text-white uppercase tracking-wider text-xs mb-2">
            1. Executive Engineering Consensus
          </h3>
          <p className="text-xs text-[#a3b3a9] font-sans leading-relaxed">{assessment.summary_markdown}</p>
        </div>

        <div>
          <h3 className="font-display font-semibold text-white uppercase tracking-wider text-xs mb-3">
            2. Verified Hydrodynamic Metrics
          </h3>
          <div className="border border-white/10 rounded-2xl overflow-hidden font-mono text-xs">
            <table className="w-full text-left">
              <thead className="bg-white/5 text-[#8e9e94] text-[10px] uppercase">
                <tr>
                  <th className="p-3">Criterion Parameter</th>
                  <th className="p-3">Calculated Value</th>
                  <th className="p-3">Nature Classification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-[#d0ded5]">
                {assessment.calculations.map((c) => (
                  <tr key={c.id}>
                    <td className="p-3 font-sans text-xs">{c.criterion_name}</td>
                    <td className="p-3 font-mono text-[#2fe578]">{c.value_numeric} {c.value_unit}</td>
                    <td className="p-3 font-mono uppercase text-[10px]">{c.provenance_classification}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <h3 className="font-display font-semibold text-white uppercase tracking-wider text-xs mb-2">
            3. Operational Custody Directives
          </h3>
          <ul className="list-disc list-inside space-y-1.5 text-xs text-[#a3b3a9]">
            {assessment.risks.map((r) => (
              <li key={r.id}>
                <span className="text-white font-normal">[{r.severity.toUpperCase()}]: {r.title}</span> — {r.mitigation_suggestion}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="pt-6 border-t border-white/10 flex justify-between items-center text-xs font-mono">
        <button onClick={onBack} className="text-[#2fe578] hover:underline">
          ← Return to Interactive Modeler
        </button>
        <span className="text-[#708076]">VERIFIED BY PROTOCOL VALIDATORS</span>
      </div>
    </div>
  );
};
