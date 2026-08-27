import React from 'react';

interface RiskGaugeProps {
  score: number;
  policyDecision?: string;
  size?: number;
  showDetails?: boolean;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  policyDecision,
  size = 120,
  showDetails = true,
}) => {
  const normalizedScore = Math.max(0, Math.min(100, score));
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 75) return '#EF4444'; // Critical
    if (s >= 60) return '#F97316'; // High
    if (s >= 40) return '#EAB308'; // Medium
    return '#22C55E'; // Low
  };

  const color = getColor(normalizedScore);

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            style={{ transition: 'stroke-dashoffset 0.8s ease-out, stroke 0.5s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold font-mono text-white">
            {Math.round(normalizedScore)}
          </span>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">/ 100</span>
        </div>
      </div>
      {showDetails && policyDecision && (
        <span
          className="mt-2 text-xs font-semibold px-2.5 py-1 rounded-full uppercase tracking-wide"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {policyDecision}
        </span>
      )}
    </div>
  );
};
