import React from 'react';

interface ProvenanceBadgeProps {
  nature: 'measured' | 'calculated' | 'estimated' | 'assumed' | 'default';
  source?: string;
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({ nature, source }) => {
  const styles = {
    measured: 'bg-[#2fe578]/10 text-[#2fe578] border-[#2fe578]/30',
    calculated: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    estimated: 'bg-amber-400/10 text-amber-300 border-amber-400/30',
    assumed: 'bg-teal-400/10 text-teal-300 border-teal-400/30',
    default: 'bg-white/5 text-[#a3b3a9] border-white/10',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono uppercase tracking-wider border ${styles[nature] || styles.default}`}
      title={source ? `Custody Source: ${source}` : undefined}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80 animate-pulse"></span>
      {nature}
    </span>
  );
};
