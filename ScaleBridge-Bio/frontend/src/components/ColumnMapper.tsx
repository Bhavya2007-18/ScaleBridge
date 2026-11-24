import React, { useState } from 'react';

interface ColumnMapping {
  sourceColumn: string;
  standardParameter: string;
  unit: string;
}

interface ColumnMapperProps {
  headers: string[];
  onSaveMappings: (mappings: ColumnMapping[]) => void;
}

const STANDARD_PARAMETERS = [
  'time_hours',
  'bioreactor_temperature_c',
  'dissolved_oxygen_percent',
  'ph',
  'agitation_rpm',
  'aeration_flow_slpm',
  'oxygen_enrichment_flow_slpm',
  'viable_cell_density_1e6_ml',
  'viability_percent',
  'glucose_g_l',
  'lactate_g_l',
  'titer_g_l',
];

export const ColumnMapper: React.FC<ColumnMapperProps> = ({ headers, onSaveMappings }) => {
  const [mappings, setMappings] = useState<Record<string, { param: string; unit: string }>>({});

  const handleSelectParam = (header: string, param: string) => {
    setMappings((prev) => ({
      ...prev,
      [header]: { ...prev[header], param },
    }));
  };

  const handleUnitChange = (header: string, unit: string) => {
    setMappings((prev) => ({
      ...prev,
      [header]: { ...prev[header], unit },
    }));
  };

  const handleSave = () => {
    const result: ColumnMapping[] = Object.entries(mappings)
      .filter(([_, val]) => val.param)
      .map(([header, val]) => ({
        sourceColumn: header,
        standardParameter: val.param,
        unit: val.unit || '',
      }));
    onSaveMappings(result);
  };

  return (
    <div className="bg-white p-5 border border-slate-200 rounded-lg space-y-4">
      <h3 className="font-semibold text-slate-800 text-sm">Map Raw Data Headers to Scientific Ontology</h3>
      <div className="space-y-3">
        {headers.map((header) => (
          <div key={header} className="flex items-center gap-3">
            <span className="w-1/3 font-mono text-xs text-slate-700 truncate" title={header}>
              {header}
            </span>
            <select
              className="w-1/3 text-xs border border-slate-300 rounded p-1.5"
              value={mappings[header]?.param || ''}
              onChange={(e) => handleSelectParam(header, e.target.value)}
            >
              <option value="">-- Ignore Column --</option>
              {STANDARD_PARAMETERS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Unit (e.g. rpm, %, g/L)"
              className="w-1/3 text-xs border border-slate-300 rounded p-1.5"
              value={mappings[header]?.unit || ''}
              onChange={(e) => handleUnitChange(header, e.target.value)}
            />
          </div>
        ))}
      </div>
      <button
        onClick={handleSave}
        className="px-4 py-2 bg-indigo-600 text-white rounded text-xs font-semibold hover:bg-indigo-700"
      >
        Confirm Column Mappings
      </button>
    </div>
  );
};
