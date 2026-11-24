import React from 'react';

export const DemoDataBanner: React.FC = () => {
  return (
    <div className="bg-[#0b130e] border-b border-white/5 py-2 px-6 flex items-center justify-between text-xs font-mono text-[#8e9e94]">
      <div className="flex items-center gap-3">
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2fe578] opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#2fe578]"></span>
        </span>
        <span className="text-[#e3e9e5] tracking-wide font-medium">SOVEREIGN LEDGER ACTIVE</span>
        <span className="text-white/20">/</span>
        <span className="text-[#a4b4aa]">CHO Cell Line #4088 (Synthetic Verification Seed)</span>
      </div>
      <div className="hidden md:flex items-center gap-4 text-[11px] text-[#708076]">
        <span>GENESIS BLOCK: 0x98AF...33B1</span>
        <span>PROOF: DETERMINISTIC HYDRAULIC AUDIT</span>
      </div>
    </div>
  );
};
