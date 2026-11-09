import { riskColor } from './ui';

/** Semi-circular gauge for a 0–100 deterministic risk score. */
export default function RiskGauge({ score, level }: { score: number; level?: string }) {
  const clamped = Math.max(0, Math.min(100, Number.isFinite(score) ? score : 0));
  const radius = 70;
  const circumference = Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);
  const color = riskColor(clamped);

  return (
    <div className="flex flex-col items-center" role="img" aria-label={`Risk score ${clamped} of 100`}>
      <svg viewBox="0 0 180 100" className="w-full max-w-[220px]">
        <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#1e293b" strokeWidth="14" strokeLinecap="round" />
        <path
          d="M 20 90 A 70 70 0 0 1 160 90"
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 600ms ease-out' }}
        />
        <text x="90" y="78" textAnchor="middle" className="fill-white" fontSize="30" fontWeight="600">
          {Math.round(clamped)}
        </text>
        <text x="90" y="96" textAnchor="middle" fill="#94a3b8" fontSize="10" letterSpacing="1.5">
          / 100
        </text>
      </svg>
      {level && (
        <span className="mt-1 text-xs font-semibold uppercase tracking-widest" style={{ color }}>
          {level} risk
        </span>
      )}
    </div>
  );
}
