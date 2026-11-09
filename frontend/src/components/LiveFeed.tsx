import { CreditCard, Radio, Webhook } from 'lucide-react';
import { LiveEvent } from '../types/api';
import { formatInr, SCENARIO_LABELS, STAGE_LABELS, verdictOf } from '../utils/liveMetrics';
import { cx, DecisionBadge, Pill, riskColor } from './ui';

const SOURCE_ICON: Record<string, JSX.Element> = {
  generator: <Radio className="h-3.5 w-3.5 text-slate-500" aria-label="Synthetic generator" />,
  razorpay: <CreditCard className="h-3.5 w-3.5 text-sky-400" aria-label="Razorpay" />,
  api: <Webhook className="h-3.5 w-3.5 text-indigo-300" aria-label="Webhook API" />,
};

export function VerdictBadge({ event }: { event: LiveEvent }) {
  if (event.outcome === 'REJECTED') {
    return <Pill tone="bg-violet-500/15 text-violet-300 ring-violet-500/30">Rejected</Pill>;
  }
  return <DecisionBadge decision={event.decision} />;
}

export default function LiveFeed({
  events,
  onSelect,
  selectedSeq,
}: {
  events: LiveEvent[];
  onSelect: (e: LiveEvent) => void;
  selectedSeq?: number;
}) {
  if (events.length === 0) {
    return <p className="px-5 py-14 text-center text-sm text-slate-500">Waiting for traffic…</p>;
  }
  return (
    <div className="max-h-[520px] overflow-auto">
      <table className="min-w-full text-sm">
        <thead className="sticky top-0 z-10 bg-slate-900">
          <tr className="border-b border-slate-800 text-left text-[11px] uppercase tracking-wider text-slate-500">
            <th className="px-4 py-2.5 font-medium">Time</th>
            <th className="px-4 py-2.5 font-medium">Event</th>
            <th className="px-4 py-2.5 text-right font-medium">Amount</th>
            <th className="px-4 py-2.5 font-medium">Risk</th>
            <th className="px-4 py-2.5 font-medium">Signal</th>
            <th className="px-4 py-2.5 font-medium">Verdict</th>
            <th className="px-4 py-2.5 text-right font-medium">Latency</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {events.map((e) => {
            const v = verdictOf(e);
            return (
              <tr
                key={e.seq}
                data-testid="live-row"
                onClick={() => onSelect(e)}
                className={cx(
                  'animate-row-in cursor-pointer transition-colors hover:bg-slate-800/40',
                  selectedSeq === e.seq && 'bg-indigo-500/10',
                  v === 'REJECTED' && 'bg-violet-500/[0.04]',
                  v === 'BLOCK' && 'bg-rose-500/[0.04]',
                )}
              >
                <td className="whitespace-nowrap px-4 py-2 font-mono text-[11px] text-slate-500">
                  {new Date(e.ts).toLocaleTimeString()}
                </td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    {SOURCE_ICON[e.source] ?? SOURCE_ICON.api}
                    <span className="truncate text-xs text-slate-200">
                      {SCENARIO_LABELS[e.scenario ?? ''] ?? e.event_type ?? 'Payment'}
                    </span>
                  </div>
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-right font-mono text-xs tabular-nums text-slate-300">
                  {formatInr(e.amount)}
                </td>
                <td className="px-4 py-2">
                  {typeof e.risk_score === 'number' ? (
                    <span className="font-mono text-xs font-semibold tabular-nums" style={{ color: riskColor(e.risk_score) }}>
                      {Math.round(e.risk_score)}
                    </span>
                  ) : (
                    <span className="text-xs text-slate-600">—</span>
                  )}
                </td>
                <td className="px-4 py-2 text-xs">
                  {e.outcome === 'REJECTED' ? (
                    <span className="text-violet-300">{STAGE_LABELS[e.rejected_stage ?? 'unknown'] ?? e.rejected_stage}</span>
                  ) : e.zombie ? (
                    <span className="text-fuchsia-300">Zombie · {e.zombie.recommendation}</span>
                  ) : e.risk_factors && e.risk_factors.length ? (
                    <span className="text-amber-300">{e.risk_factors.join(', ')}</span>
                  ) : (
                    <span className="text-slate-600">—</span>
                  )}
                </td>
                <td className="px-4 py-2">
                  <VerdictBadge event={e} />
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-right font-mono text-[11px] tabular-nums text-slate-500">
                  {typeof e.latency_ms === 'number' ? `${e.latency_ms.toFixed(1)} ms` : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
