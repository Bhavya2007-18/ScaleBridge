import React from 'react';
import { useProjects } from '../api/hooks/useData';
import { Project } from '../api/types';

interface ProjectsProps {
  onSelectProject: (p: Project) => void;
}

export const Projects: React.FC<ProjectsProps> = ({ onSelectProject }) => {
  const { projects, loading, error } = useProjects();

  return (
    <div className="space-y-12">
      {/* Editorial Hero Banner */}
      <div className="relative rounded-3xl p-8 md:p-12 overflow-hidden border border-white/10 bg-gradient-to-br from-[#121c16]/80 via-[#0d1611]/60 to-[#080c09] backdrop-blur-xl">
        <div className="absolute -right-16 -top-16 w-80 h-80 rounded-full bg-[#2fe578]/10 blur-3xl pointer-events-none"></div>
        
        <div className="max-w-2xl relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-mono uppercase tracking-widest text-[#2fe578] mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2fe578]"></span>
            Bioprocess Master Index
          </div>
          <h1 className="text-3xl md:text-5xl font-display font-extrabold text-white tracking-tight leading-tight">
            Verifiable Bioprocess Passports & Scale Registries.
          </h1>
          <p className="mt-4 text-sm md:text-base text-[#a3b3a9] font-light leading-relaxed">
            Preserve immutable records of cellular growth kinetics, hydrodynamic models, and vessel scale-up credentials. Grounded in deterministic biophysics.
          </p>
        </div>

        <div className="mt-8 pt-8 border-t border-white/5 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono text-[#8e9e94]">
          <div>
            <div className="text-[10px] uppercase text-[#708076]">VERIFIED STRAINS</div>
            <div className="text-xl font-display font-bold text-white mt-1">24 Active</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-[#708076]">MAX CAPACITY RECORD</div>
            <div className="text-xl font-display font-bold text-[#2fe578] mt-1">10,000 L</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-[#708076]">RISK PREVENTIONS</div>
            <div className="text-xl font-display font-bold text-white mt-1">100%</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-[#708076]">AUDIT STANDARD</div>
            <div className="text-xl font-display font-bold text-[#7cf6b1] mt-1">ICH Q8 / Q9</div>
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-display font-bold text-white">Active Transfer Passports</h2>
            <p className="text-xs text-[#8e9e94] mt-0.5 font-light">Select a cell passport to inspect critical parameters or initiate hydrodynamic scale-up.</p>
          </div>
          <span className="text-xs font-mono text-[#708076]">SORT BY: RECENT DEPLOYMENTS</span>
        </div>

        {loading && <div className="text-xs font-mono text-[#708076] py-12 text-center">Reading on-chain ledger entries...</div>}
        {error && <div className="text-xs font-mono text-rose-400 py-6 text-center">[Registry Sync Error]: {error}</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              onClick={() => onSelectProject(proj)}
              className="group p-6 rounded-3xl euronium-glass-card cursor-pointer transition-all duration-300 relative flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between text-xs font-mono mb-4">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#2fe578]/10 border border-[#2fe578]/30 text-[#2fe578] text-[10px] uppercase tracking-wider font-semibold">
                    {proj.organism}
                  </span>
                  <span className="text-[10px] text-[#708076]">EXP: 2026-11</span>
                </div>

                <h3 className="text-lg font-display font-bold text-white group-hover:text-[#2fe578] transition">
                  {proj.name}
                </h3>
                <p className="mt-2 text-xs text-[#a3b3a9] font-light line-clamp-2 leading-relaxed">
                  {proj.description || 'Target molecule scale-up verification from micro-titer seed to pilot manufacturing node.'}
                </p>
              </div>

              <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-xs font-mono text-[#8e9e94]">
                <span>MOLECULE: <strong className="text-white font-normal">{proj.target_molecule}</strong></span>
                <span className="text-[#2fe578] group-hover:translate-x-1 transition duration-200">Open Passport →</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
