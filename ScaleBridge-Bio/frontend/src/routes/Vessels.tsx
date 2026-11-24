import React from 'react';
import { useVessels } from '../api/hooks/useData';

export const Vessels: React.FC = () => {
  const { vessels, loading, error } = useVessels();

  if (loading) return <div className="p-8 text-center text-sm text-slate-500">Loading vessel profiles...</div>;
  if (error) return <div className="p-8 text-center text-sm text-rose-500">Error: {error}</div>;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Bioreactor Equipment Profiles</h1>
          <p className="text-sm text-slate-500">Curated hardware geometry, impeller configurations, and utility limits.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {vessels.map((v) => (
          <div key={v.id} className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                {v.scale_category}
              </span>
              <span className="text-xs text-slate-400">{v.facility || 'Facility unspecified'}</span>
            </div>
            <h3 className="font-semibold text-slate-900 text-base">{v.name}</h3>
            <div className="space-y-1 text-xs text-slate-600">
              <div className="flex justify-between">
                <span>Working Volume:</span>
                <span className="font-medium text-slate-800">{v.working_volume_min_l} - {v.working_volume_max_l} L</span>
              </div>
              <div className="flex justify-between">
                <span>Max Agitation:</span>
                <span className="font-medium text-slate-800">{v.max_rpm ?? '—'} RPM</span>
              </div>
              <div className="flex justify-between">
                <span>Motor Rating:</span>
                <span className="font-medium text-slate-800">{v.max_power_w ?? '—'} W</span>
              </div>
              <div className="flex justify-between">
                <span>Impellers:</span>
                <span className="font-medium text-slate-800 truncate" title={v.impeller_types.join(', ')}>
                  {v.impeller_types.join(', ')}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
