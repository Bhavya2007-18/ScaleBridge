import React from 'react';
import { Project } from '../api/types';

interface ProcessPassportProps {
  project: Project;
}

export const ProcessPassport: React.FC<ProcessPassportProps> = ({ project }) => {
  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="border-b border-slate-200 pb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded">
            Validated Passport v1.0
          </span>
        </div>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">{project.name}</h1>
        <p className="text-sm text-slate-500">{project.description}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-4">
          <h3 className="font-semibold text-slate-800 text-sm border-b pb-2">Critical Process Parameters (CPPs)</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Culture Temperature</span>
              <span className="font-mono font-medium">36.8 ± 0.2 °C</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">pH Setpoint</span>
              <span className="font-mono font-medium">7.10 (deadband 0.05)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Dissolved Oxygen (dO2)</span>
              <span className="font-mono font-medium">40.0% saturation</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Target Power Density (P/V)</span>
              <span className="font-mono font-medium">120 W/m³</span>
            </div>
          </div>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-sm space-y-4">
          <h3 className="font-semibold text-slate-800 text-sm border-b pb-2">Critical Quality Attributes (CQAs)</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Harvest Titer</span>
              <span className="font-mono font-medium">≥ 3.5 g/L</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Cell Viability at Harvest</span>
              <span className="font-mono font-medium">≥ 85.0%</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-600">Monomer Content (SEC-HPLC)</span>
              <span className="font-mono font-medium">≥ 95.0%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
