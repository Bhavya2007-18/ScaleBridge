import React from 'react';
import { Assessment } from '../api/types';
import { RiskRegister } from '../components/RiskRegister';
import { ProvenanceBadge } from '../components/ProvenanceBadge';

interface AssessmentResultsProps {
  assessment: Assessment;
  onGenerateReport: () => void;
}

export const AssessmentResults: React.FC<AssessmentResultsProps> = ({
  assessment,
  onGenerateReport,
}) => {
  return (
    <div className="space-y-8">
      {/* Overall Readiness Header Card */}
      <div className="p-8 md:p-10 rounded-3xl euronium-glass-card border border-white/10 relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="max-w-xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-2 h-2 rounded-full bg-[#2fe578]"></span>
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#2fe578]">
              SCALE READINESS VERIFICATION // PROTOCOL AUDITED
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-display font-extrabold text-white">
            Transfer Feasibility Consensus
          </h1>
          <p className="mt-2 text-xs md:text-sm text-[#a3b3a9] font-light leading-relaxed">
            {assessment.summary_markdown}
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/10 text-center md:text-right shrink-0">
          <div className="text-[10px] font-mono uppercase tracking-widest text-[#708076]">READINESS INDEX</div>
          <div className="text-5xl font-display font-extrabold text-[#2fe578] mt-1">
            {assessment.overall_readiness_score.toFixed(1)}
            <span className="text-lg text-[#708076] font-normal"> / 100</span>
          </div>
          <div className="mt-2 text-[10px] font-mono text-[#7cf6b1]">STATUS: TECHNICAL PASS</div>
        </div>
      </div>

      {/* Hydrodynamic Metric Cards */}
      <div className="space-y-4">
        <h3 className="text-sm font-display font-semibold text-white uppercase tracking-wider">
          Governing Biophysical Quantities
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {assessment.calculations.map((c) => (
            <div key={c.id} className="p-6 rounded-3xl euronium-glass-card space-y-4 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono text-[#8e9e94] uppercase tracking-wider">{c.criterion_name}</span>
                  <ProvenanceBadge nature={c.provenance_classification} />
                </div>
                <div className="text-3xl font-display font-bold text-white">
                  {c.value_numeric ?? '—'} <span className="text-sm font-mono text-[#2fe578] font-normal">{c.value_unit}</span>
                </div>
              </div>

              {c.assumptions.length > 0 && (
                <div className="pt-3 border-t border-white/5 text-[11px] font-mono text-[#708076]">
                  <strong className="text-[#a3b3a9] font-normal">Assumptions:</strong> {c.assumptions.join('; ')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Risk Register */}
      <div className="space-y-4">
        <h3 className="text-sm font-display font-semibold text-white uppercase tracking-wider">
          Explainable Risk Flags & Safeguards
        </h3>
        <RiskRegister risks={assessment.risks} />
      </div>

      {/* Validation Checklist */}
      <div className="space-y-4">
        <h3 className="text-sm font-display font-semibold text-white uppercase tracking-wider">
          Consensus Validation Milestones
        </h3>
        <div className="space-y-3">
          {assessment.validation_tasks.map((task) => (
            <div key={task.id} className="p-5 rounded-2xl euronium-glass-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-[#2fe578] bg-[#2fe578]/10 px-2 py-0.5 rounded">
                    {task.phase.replace('_', ' ')}
                  </span>
                  <h4 className="font-display font-semibold text-sm text-white">{task.task_name}</h4>
                </div>
                <p className="text-xs text-[#a3b3a9] font-light">{task.description}</p>
                <div className="mt-2 text-xs font-mono text-[#7cf6b1]">
                  Criteria: {task.success_criteria}
                </div>
              </div>
              <span className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-mono text-[#8e9e94] shrink-0 self-start sm:self-center">
                {task.is_completed ? 'CONFIRMED' : 'AWAITING QUAL'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Button */}
      <div className="pt-6 border-t border-white/5 flex justify-end">
        <button
          onClick={onGenerateReport}
          className="px-8 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-white font-mono text-xs uppercase tracking-wider font-semibold transition"
        >
          Publish Official Bioprocess Transfer Report →
        </button>
      </div>
    </div>
  );
};
