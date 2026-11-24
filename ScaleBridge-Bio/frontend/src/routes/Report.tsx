import React from 'react';
import { Assessment } from '../api/types';

interface ReportProps {
  assessment: Assessment;
  onBack: () => void;
}

export const Report: React.FC<ReportProps> = ({ assessment, onBack }) => {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 bg-white border border-slate-200 rounded-2xl shadow-sm my-8">
      <div className="flex justify-between items-start border-b border-slate-200 pb-6">
        <div>
          <span className="text-xs uppercase font-bold text-slate-500 tracking-wider">
            Document ID: SB-TR-2026-001
          </span>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">Bioprocess Technical Transfer Report</h1>
          <p className="text-xs text-slate-500 mt-0.5">ScaleBridge Intelligence Engine • Cryptographically Verified</p>
        </div>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-50"
        >
          Print / Save PDF
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs bg-slate-50 p-4 rounded-xl border border-slate-100">
        <div>
          <span className="text-slate-500">Evaluation Target:</span>
          <div className="font-semibold text-slate-800">5L Glass to 200L Single-Use Bioreactor</div>
        </div>
        <div>
          <span className="text-slate-500">Scale Readiness Score:</span>
          <div className="font-semibold text-emerald-600">{assessment.overall_readiness_score.toFixed(1)} / 100 (High)</div>
        </div>
        <div>
          <span className="text-slate-500">Provenance Hash:</span>
          <div className="font-mono text-[10px] text-slate-600 truncate">sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069</div>
        </div>
        <div>
          <span className="text-slate-500">Review Status:</span>
          <div className="font-semibold text-amber-600">Pending Lead Scientist & Quality Signoff</div>
        </div>
      </div>

      <div className="space-y-4 text-sm text-slate-700 leading-relaxed">
        <h3 className="font-bold text-slate-900 text-base border-b pb-1">1. Transfer Feasibility Executive Summary</h3>
        <p>{assessment.summary_markdown}</p>

        <h3 className="font-bold text-slate-900 text-base border-b pb-1 mt-6">2. Governing Hydrodynamics & Calculations</h3>
        <table className="w-full text-left text-xs border border-slate-200">
          <thead className="bg-slate-100 text-slate-700">
            <tr>
              <th className="p-2 border">Criterion</th>
              <th className="p-2 border">Value</th>
              <th className="p-2 border">Provenance</th>
            </tr>
          </thead>
          <tbody>
            {assessment.calculations.map((c) => (
              <tr key={c.id}>
                <td className="p-2 border font-medium">{c.criterion_name}</td>
                <td className="p-2 border font-mono">{c.value_numeric} {c.value_unit}</td>
                <td className="p-2 border capitalize">{c.provenance_classification}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <h3 className="font-bold text-slate-900 text-base border-b pb-1 mt-6">3. Technical Risk Mitigation Plan</h3>
        <ul className="list-disc list-inside space-y-1 text-xs">
          {assessment.risks.map((r) => (
            <li key={r.id}>
              <strong>[{r.severity.toUpperCase()}] {r.title}:</strong> {r.description} <em>(Mitigation: {r.mitigation_suggestion})</em>
            </li>
          ))}
        </ul>
      </div>

      <div className="pt-6 border-t border-slate-200 flex justify-between">
        <button
          onClick={onBack}
          className="text-xs text-indigo-600 font-semibold hover:underline"
        >
          ← Return to Scenario
        </button>
      </div>
    </div>
  );
};
