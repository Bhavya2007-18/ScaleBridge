import React from 'react';

export const DemoDataBanner: React.FC = () => {
  return (
    <div className="bg-indigo-900 text-indigo-100 text-xs px-4 py-2 flex items-center justify-between border-b border-indigo-800">
      <div className="flex items-center gap-2">
        <span className="bg-indigo-700 uppercase px-2 py-0.5 rounded text-[10px] font-bold tracking-wider">
          Synthetic Demo Dataset
        </span>
        <span>
          Showing preloaded mammalian CHO scale-up transfer (5L benchtop glass to 200L single-use bioreactor).
        </span>
      </div>
      <span className="text-indigo-300">ScaleBridge Intelligence Engine v1.0</span>
    </div>
  );
};
