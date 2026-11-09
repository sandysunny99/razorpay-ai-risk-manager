import { KeyboardEvent } from 'react';
import { LiveEvent } from '../types/api';
import { eventLabel, formatInr, STAGE_LABELS, verdictOf } from '../utils/liveMetrics';
import { cx, DecisionTag, riskColor, Tag } from './ui';

const SOURCE_LABEL: Record<string, string> = {
  generator: 'Synthetic',
  razorpay: 'Razorpay',
  youpi: 'YouPI UPI',
  api: 'Webhook API',
};

export function VerdictTag({ event }: { event: LiveEvent }) {
  if (event.outcome === 'REJECTED') return <Tag outline tone="block">Rejected</Tag>;
  return <DecisionTag decision={event.decision} />;
}

export function signalText(e: LiveEvent): { text: string; tone: string } | null {
  if (e.outcome === 'REJECTED') return { text: STAGE_LABELS[e.rejected_stage ?? 'unknown'] ?? 'Ingress', tone: 'text-block' };
  if (e.threat?.some((m) => m.category === 'card_exposed')) return { text: 'Card exposed', tone: 'text-zombie' };
  if (e.zombie) return { text: `Zombie: ${e.zombie.recommendation.replace(/_/g, ' ').toLowerCase()}`, tone: 'text-zombie' };
  if (e.threat?.length) return { text: `Intel: ${e.threat[0].category.replace(/_/g, ' ')}`, tone: 'text-review' };
  if (e.risk_factors?.length) return { text: e.risk_factors.join(', ').replace(/_/g, ' '), tone: 'text-ink-muted' };
  return null;
}

export default function LiveFeed({
  events,
  onSelect,
  selectedSeq,
  emptyMessage,
}: {
  events: LiveEvent[];
  onSelect: (e: LiveEvent) => void;
  selectedSeq?: number;
  emptyMessage: string;
}) {
  if (events.length === 0) {
    return <p className="px-4 py-12 text-center text-sm text-ink-subtle">{emptyMessage}</p>;
  }
  const onKey = (e: KeyboardEvent, ev: LiveEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(ev);
    }
  };
  return (
    <div className="max-h-[560px] overflow-auto">
      <table className="min-w-full text-sm">
        <thead className="sticky top-0 z-10 bg-surface">
          <tr className="border-b border-line text-left text-xs text-ink-subtle">
            <th className="px-4 py-2 font-medium">Verdict</th>
            <th className="px-4 py-2 font-medium">Why</th>
            <th className="px-4 py-2 text-right font-medium">Amount</th>
            <th className="px-4 py-2 text-right font-medium">Risk</th>
            <th className="px-4 py-2 font-medium">Event</th>
            <th className="px-4 py-2 font-medium">Time</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => {
            const sig = signalText(e);
            return (
              <tr
                key={e.seq}
                data-testid="live-row"
                tabIndex={0}
                aria-label={`${eventLabel(e)}, ${verdictOf(e).toLowerCase()}, open details`}
                onClick={() => onSelect(e)}
                onKeyDown={(k) => onKey(k, e)}
                className={cx(
                  'animate-row-in cursor-pointer border-b border-line/60 hover:bg-raised focus-visible:bg-raised',
                  selectedSeq === e.seq && 'bg-raised',
                )}
              >
                <td className="px-4 py-2">
                  <VerdictTag event={e} />
                </td>
                <td className={cx('max-w-[220px] truncate px-4 py-2', sig?.tone ?? 'text-ink-subtle')}>{sig?.text ?? 'No signal'}</td>
                <td className="whitespace-nowrap px-4 py-2 text-right font-mono tabular-nums text-ink">{formatInr(e.amount)}</td>
                <td className="px-4 py-2 text-right font-mono tabular-nums">
                  {typeof e.risk_score === 'number' ? (
                    <span style={{ color: riskColor(e.risk_score) }}>{Math.round(e.risk_score)}</span>
                  ) : (
                    <span className="text-ink-subtle">–</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-ink-muted">
                  {eventLabel(e)}
                  <span className="ml-2 text-xs text-ink-subtle">{SOURCE_LABEL[e.source] ?? e.source}</span>
                </td>
                <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-ink-subtle">{new Date(e.ts).toLocaleTimeString()}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
