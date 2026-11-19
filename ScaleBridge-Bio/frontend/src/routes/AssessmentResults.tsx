import React from 'react';
import { Assessment } from '../api/types';
import { RiskRegister } from '../components/RiskRegister';
import { ValidationPlanList } from '../components/ValidationPlanList';
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
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      {/* Header with Readiness Score */}
      <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm flex items-center justify-between">
        <div>
          <span className="text-xs uppercase font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded">
            Scale-Up Evaluation Status: {assessment.status.toUpperCase()}
          </span>
          <h1 className="mt-2 text-2xl font-bold text-slate-900">Transfer Feasibility Assessment</h1>
          <p className="mt-1 text-sm text-slate-500">{assessment.summary_markdown}</p>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase font-bold text-slate-400">Scale Readiness Score</div>
          <div className="text-4xl font-extrabold text-indigo-600">
            {assessment.overall_readiness_score.toFixed(1)}
            <span className="text-lg text-slate-400 font-normal"> / 100</span>
          </div>
        </div>
      </div>

      {/* Engineering Calculations */}
      <div className="space-y-4">
        <h3 className="font-semibold text-slate-900 text-lg">Engineering Predictions & Hydrodynamics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {assessment.calculations.map((c) => (
            <div key={c.id} className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-slate-600">{c.criterion_name}</span>
                <ProvenanceBadge nature={c.provenance_classification} />
              </div>
              <div className="text-2xl font-bold text-slate-900">
                {c.value_numeric ?? '—'} <span className="text-sm font-normal text-slate-500">{c.value_unit}</span>
              </div>
              {c.assumptions.length > 0 && (
                <div className="text-[11px] text-slate-500 border-t pt-2">
                  <strong>Assumptions:</strong> {c.assumptions.join('; ')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Multi-Parametric Risk Register */}
      <div className="space-y-4">
        <h3 className="font-semibold text-slate-900 text-lg">Explainable Risk Flags</h3>
        <RiskRegister risks={assessment.risks} />
      </div>

      {/* Validation Milestones */}
      <div className="space-y-4">
        <h3 className="font-semibold text-slate-900 text-lg">Recommended Validation Plan</h3>
        <ValidationPlanList tasks={assessment.validation_tasks} />
      </div>

      {/* Export Action */}
      <div className="pt-4 flex justify-end">
        <button
          onClick={onGenerateReport}
          className="px-6 py-3 bg-slate-900 text-white rounded-xl font-semibold text-sm hover:bg-slate-800 shadow-md transition"
        >
          Generate Official Tech-Transfer Report →
        </button>
      </div>
    </div>
  );
};
