import { ReactNode, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { X } from 'lucide-react';
import { LiveEvent } from '../types/api';
import { formatInr, SCENARIO_LABELS } from '../utils/liveMetrics';
import PipelineTimeline, { allPassed, failedAt, StageId, StageStatus } from './PipelineTimeline';
import RiskGauge from './RiskGauge';
import { VerdictBadge } from './LiveFeed';
import { Notice, RiskLevelBadge } from './ui';

const STAGE_IDS: StageId[] = ['hmac', 'schema', 'tenant', 'pan', 'replay', 'idempotency'];

export function pipelineFor(event: LiveEvent): Record<StageId, StageStatus> {
  if (event.outcome === 'REJECTED') {
    const stage = STAGE_IDS.find((s) => s === event.rejected_stage) ?? 'schema';
    return failedAt(stage);
  }
  const st = allPassed();
  if (!event.ai_provider || event.ai_provider === 'UNAVAILABLE') st.ai = 'fallback';
  return st;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className="mt-0.5 break-all text-sm text-slate-200">{children}</dd>
    </div>
  );
}

export default function EventDrawer({ event, onClose }: { event: LiveEvent | null; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  if (!event) return null;
  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Event details">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <aside className="absolute inset-y-0 right-0 flex w-full max-w-md flex-col border-l border-slate-800 bg-slate-950 shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-800 px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-500">{event.source} event</p>
            <h2 className="mt-0.5 text-base font-semibold text-white">{SCENARIO_LABELS[event.scenario ?? ''] ?? event.event_type ?? 'Payment'}</h2>
          </div>
          <div className="flex items-center gap-3">
            <VerdictBadge event={event} />
            <button onClick={onClose} className="rounded p-1 text-slate-400 hover:text-white" aria-label="Close details">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5">
          {event.outcome === 'REJECTED' ? (
            <Notice tone="error">
              Rejected with HTTP {event.http_status}: {event.reason}. No risk score, AI call or audit record is produced for traffic
              that fails ingress security.
            </Notice>
          ) : (
            <div className="grid grid-cols-2 items-center gap-4">
              <RiskGauge score={event.risk_score ?? 0} level={event.risk_level} />
              <dl className="space-y-3">
                <Field label="Decision">{event.decision}</Field>
                <Field label="Risk level"><RiskLevelBadge level={event.risk_level} /></Field>
                <Field label="Factors">{event.risk_factors?.length ? event.risk_factors.join(', ') : 'None'}</Field>
              </dl>
            </div>
          )}

          {event.zombie && (
            <div className="rounded-lg border border-fuchsia-500/30 bg-fuchsia-500/10 p-4 text-sm">
              <p className="font-semibold text-fuchsia-200">Zombie Card Saver · {event.zombie.severity}</p>
              <p className="mt-1 text-fuchsia-100/80">{event.zombie.impact}</p>
              <p className="mt-2 font-mono text-xs text-fuchsia-200">→ {event.zombie.recommendation}</p>
            </div>
          )}

          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">Pipeline</h3>
            <PipelineTimeline status={pipelineFor(event)} />
          </section>

          <dl className="grid grid-cols-2 gap-4">
            <Field label="Amount">{formatInr(event.amount)}</Field>
            <Field label="Latency">{event.latency_ms != null ? `${event.latency_ms.toFixed(2)} ms` : '—'}</Field>
            <Field label="AI advisory">{event.ai_provider ?? '—'}</Field>
            <Field label="Received">{new Date(event.ts).toLocaleString()}</Field>
            <Field label="Event ID"><code className="text-xs">{event.event_id ?? '—'}</code></Field>
            <Field label="Correlation ID"><code className="text-xs">{event.correlation_id ?? '—'}</code></Field>
          </dl>

          {event.audit_id && (
            <Link
              to={`/ledger?id=${encodeURIComponent(event.audit_id)}`}
              className="block rounded-lg border border-slate-700 px-4 py-2.5 text-center text-sm font-medium text-indigo-200 hover:bg-slate-800"
            >
              Verify in audit ledger →
            </Link>
          )}
        </div>
      </aside>
    </div>
  );
}
