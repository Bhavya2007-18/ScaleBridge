import React from 'react';

interface InsufficientEvidenceProps {
  parameter: string;
  missingRequirements: string[];
}

export const InsufficientEvidence: React.FC<InsufficientEvidenceProps> = ({
  parameter,
  missingRequirements,
}) => {
  return (
    <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-amber-900 text-sm">
      <div className="flex items-center gap-2 font-medium">
        <span>⚠️ Insufficient Evidence: {parameter}</span>
      </div>
      <p className="mt-1 text-xs text-amber-700">
        Calculation suspended to prevent hallucinated engineering values. Required missing inputs:
      </p>
      <ul className="mt-1 list-disc list-inside text-xs text-amber-800">
        {missingRequirements.map((req, idx) => (
          <li key={idx}>{req}</li>
        ))}
      </ul>
    </div>
  );
};
