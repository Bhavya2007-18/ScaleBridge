import React from 'react';
import { useProjects } from '../api/hooks/useData';
import { Project } from '../api/types';

interface ProjectsProps {
  onSelectProject: (p: Project) => void;
}

export const Projects: React.FC<ProjectsProps> = ({ onSelectProject }) => {
  const { projects, loading, error } = useProjects();

  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading projects...</div>;
  if (error) return <div className="p-8 text-center text-sm text-rose-500">Error: {error}</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Scale-Up Projects</h1>
          <p className="text-sm text-slate-500">Select a bioprocess transfer project to review or model.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((proj) => (
          <div
            key={proj.id}
            onClick={() => onSelectProject(proj)}
            className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:border-indigo-500 hover:shadow-md cursor-pointer transition"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-bold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-full">
                {proj.organism}
              </span>
            </div>
            <h3 className="mt-3 text-lg font-semibold text-slate-800">{proj.name}</h3>
            <p className="mt-1 text-xs text-slate-500 line-clamp-2">{proj.description}</p>
            <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between text-xs text-slate-600">
              <span>Target: <strong>{proj.target_molecule}</strong></span>
              <span className="text-indigo-600 font-semibold">Open Project →</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
