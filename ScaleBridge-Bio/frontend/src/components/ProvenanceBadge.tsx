import React from 'react';

interface ProvenanceBadgeProps {
  nature: 'measured' | 'calculated' | 'estimated' | 'assumed' | 'default';
  source?: string;
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({ nature, source }) => {
  const styles = {
    measured: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    calculated: 'bg-blue-100 text-blue-800 border-blue-300',
    estimated: 'bg-amber-100 text-amber-800 border-amber-300',
    assumed: 'bg-purple-100 text-purple-800 border-purple-300',
    default: 'bg-slate-100 text-slate-700 border-slate-300',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${styles[nature] || styles.default}`}
      title={source ? `Source: ${source}` : undefined}
    >
      {nature.toUpperCase()}
    </span>
  );
};
