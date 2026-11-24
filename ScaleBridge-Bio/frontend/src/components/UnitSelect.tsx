import React from 'react';

interface UnitSelectProps {
  value: string;
  category: 'volume' | 'speed' | 'power' | 'flow' | 'kla';
  onChange: (val: string) => void;
}

const UNITS_BY_CATEGORY: Record<string, string[]> = {
  volume: ['L', 'm³', 'mL'],
  speed: ['rpm', 'rad/s', 'm/s'],
  power: ['W', 'kW', 'hp', 'W/m³'],
  flow: ['slpm', 'vvm', 'L/min', 'm³/h'],
  kla: ['1/h', '1/s'],
};

export const UnitSelect: React.FC<UnitSelectProps> = ({ value, category, onChange }) => {
  const units = UNITS_BY_CATEGORY[category] || [];

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="text-xs border border-slate-300 rounded px-2 py-1 bg-white"
    >
      {units.map((u) => (
        <option key={u} value={u}>{u}</option>
      ))}
    </select>
  );
};
