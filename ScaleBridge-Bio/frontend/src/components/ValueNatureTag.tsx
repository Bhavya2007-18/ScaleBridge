import React from 'react';

interface ValueNatureTagProps {
  value: number | string | null | undefined;
  unit?: string;
  nature: 'measured' | 'calculated' | 'estimated' | 'assumed';
}

export const ValueNatureTag: React.FC<ValueNatureTagProps> = ({ value, unit, nature }) => {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-sm">
      <span className="font-semibold text-slate-800">{value ?? 'N/A'}</span>
      {unit && <span className="text-slate-500 text-xs">{unit}</span>}
      <span className="text-[10px] px-1 bg-slate-200 text-slate-700 rounded uppercase">
        {nature[0]}
      </span>
    </span>
  );
};
