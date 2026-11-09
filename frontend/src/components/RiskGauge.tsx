import { riskColor } from './ui';

/** Semi-circular gauge for a 0 to 100 deterministic risk score. */
export default function RiskGauge({ score, level }: { score: number; level?: string }) {
  const clamped = Math.max(0, Math.min(100, Number.isFinite(score) ? score : 0));
  const circumference = Math.PI * 70;
  const color = riskColor(clamped);

  return (
    <div className="flex flex-col items-center" role="img" aria-label={`Risk score ${clamped} of 100`}>
      <svg viewBox="0 0 180 100" width="180" height="100" className="w-full max-w-[200px]">
        <path d="M 20 90 A 70 70 0 0 1 160 90" fill="none" stroke="#2b2f35" strokeWidth="12" />
        <path
          d="M 20 90 A 70 70 0 0 1 160 90"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - clamped / 100)}
        />
        <text x="90" y="80" textAnchor="middle" fill="#ecebe7" fontSize="30" fontWeight="600" fontFamily="IBM Plex Mono, monospace">
          {Math.round(clamped)}
        </text>
      </svg>
      {level && <span className="mt-1 text-xs text-ink-muted">{level.charAt(0) + level.slice(1).toLowerCase()} risk</span>}
    </div>
  );
}
