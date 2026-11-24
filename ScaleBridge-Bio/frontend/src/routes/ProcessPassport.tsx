import React from 'react';
import { Project } from '../api/types';

interface ProcessPassportProps {
  project: Project;
}

export const ProcessPassport: React.FC<ProcessPassportProps> = ({ project }) => {
  return (
    <div className="space-y-8">
      {/* Passport Header Block */}
      <div className="p-8 rounded-3xl euronium-glass-card border border-white/10 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-[#2fe578]"></span>
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#2fe578]">
                IMMUTABLE PROCESS PASSPORT // GENESIS REV 1.0
              </span>
            </div>
            <h1 className="text-3xl font-display font-bold text-white">{project.name}</h1>
            <p className="text-xs text-[#a3b3a9] font-light mt-1 max-w-xl">{project.description}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs font-mono text-[#8e9e94]">
              ORGANISM: <span className="text-white font-medium">{project.organism}</span>
            </span>
            <span className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs font-mono text-[#8e9e94]">
              TARGET: <span className="text-[#2fe578] font-medium">{project.target_molecule}</span>
            </span>
          </div>
        </div>
      </div>

      {/* CPP & CQA Registry Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* CPP Block */}
        <div className="p-6 rounded-3xl euronium-glass-card space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-sm font-display font-semibold text-white uppercase tracking-wider">
              Critical Process Parameters (CPPs)
            </h3>
            <span className="text-[10px] font-mono text-[#2fe578]">LOCKED ENVELOPE</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">Culture Temperature</span>
              <span className="text-white font-medium">36.8 ± 0.2 °C</span>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">pH Setpoint & Control Deadband</span>
              <span className="text-white font-medium">7.10 (± 0.05)</span>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">Dissolved Oxygen (dO2)</span>
              <span className="text-white font-medium">40.0% Saturation</span>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">Nominal Specific Power Density (P/V)</span>
              <span className="text-[#2fe578] font-bold">120.0 W/m³</span>
            </div>
          </div>
        </div>

        {/* CQA Block */}
        <div className="p-6 rounded-3xl euronium-glass-card space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-sm font-display font-semibold text-white uppercase tracking-wider">
              Critical Quality Attributes (CQAs)
            </h3>
            <span className="text-[10px] font-mono text-[#7cf6b1]">VALIDATION GOALS</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">Harvest Volumetric Titer</span>
              <span className="text-white font-medium">≥ 3.50 g/L</span>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">Viability at Vessel Depletion</span>
              <span className="text-white font-medium">≥ 85.0%</span>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">Monomer Purity Fraction</span>
              <span className="text-white font-medium">≥ 95.0% (SEC-HPLC)</span>
            </div>
            <div className="flex justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <span className="text-[#8e9e94]">Peak Viable Cell Density (VCD)</span>
              <span className="text-[#2fe578] font-bold">18.5 × 10⁶ cells/mL</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
