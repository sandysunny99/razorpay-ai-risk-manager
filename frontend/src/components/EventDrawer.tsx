import { ReactNode, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { X } from 'lucide-react';
import { LiveEvent } from '../types/api';
import { eventLabel, formatInr } from '../utils/liveMetrics';
import PipelineTimeline, { allPassed, failedAt, StageId, StageStatus } from './PipelineTimeline';
import RiskGauge from './RiskGauge';
import { VerdictTag } from './LiveFeed';
import { Notice, RiskLevelTag } from './ui';

const INGRESS: StageId[] = ['hmac', 'schema', 'tenant', 'pan', 'replay', 'idempotency'];

export function pipelineFor(event: LiveEvent): Record<StageId, StageStatus> {
  if (event.outcome === 'REJECTED') {
    return failedAt(INGRESS.find((s) => s === event.rejected_stage) ?? 'schema');
  }
  const st = allPassed();
  if (!event.ai_provider || event.ai_provider === 'UNAVAILABLE') st.ai = 'fallback';
  return st;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ink-subtle">{label}</dt>
      <dd className="mt-0.5 break-all text-sm text-ink">{children}</dd>
    </div>
  );
}

export default function EventDrawer({ event, onClose }: { event: LiveEvent | null; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!event) return;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [event, onClose]);

  if (!event) return null;
  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Event details">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <aside className="absolute inset-y-0 right-0 flex w-full max-w-md flex-col border-l border-line-strong bg-surface shadow-2xl">
        <div className="flex items-start justify-between gap-3 border-b border-line px-5 py-4">
          <div>
            <p className="text-xs text-ink-subtle">Event from {event.source}</p>
            <h2 className="mt-0.5 text-base font-semibold text-ink">{eventLabel(event)}</h2>
          </div>
          <div className="flex items-center gap-3">
            <VerdictTag event={event} />
            <button ref={closeRef} onClick={onClose} className="rounded p-1 text-ink-muted hover:text-ink" aria-label="Close details">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5">
          {event.outcome === 'REJECTED' ? (
            <Notice tone="error" title={`Rejected with HTTP ${event.http_status}`}>
              {event.reason}. Traffic that fails ingress security gets no risk score, AI call or audit record.
            </Notice>
          ) : (
            <div className="grid grid-cols-2 items-center gap-4">
              <RiskGauge score={event.risk_score ?? 0} level={event.risk_level} />
              <dl className="space-y-3">
                <Field label="Decision">{event.decision}</Field>
                <Field label="Risk level"><RiskLevelTag level={event.risk_level} /></Field>
                <Field label="Factors">{event.risk_factors?.length ? event.risk_factors.join(', ').replace(/_/g, ' ') : 'None'}</Field>
              </dl>
            </div>
          )}

          {event.zombie && (
            <div className="border-l-2 border-zombie bg-zombie/10 px-4 py-3 text-sm">
              <p className="font-semibold text-zombie">Zombie Card Saver, {event.zombie.severity.toLowerCase()}</p>
              <p className="mt-1 text-ink">{event.zombie.impact}</p>
              <p className="mt-1 font-mono text-xs text-ink-muted">{event.zombie.recommendation}</p>
            </div>
          )}

          {event.threat && event.threat.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-semibold text-ink">Threat intelligence</h3>
              <ul className="space-y-1.5 text-sm">
                {event.threat.map((m, i) => (
                  <li key={i} className="flex items-center justify-between gap-3">
                    <span className="text-ink">
                      {m.category.replace(/_/g, ' ')}
                      <span className="ml-2 text-xs text-ink-subtle">{m.source}</span>
                    </span>
                    <span className="font-mono text-xs text-ink-muted">{m.indicator}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h3 className="mb-1 text-sm font-semibold text-ink">Pipeline</h3>
            <PipelineTimeline status={pipelineFor(event)} />
          </section>

          <dl className="grid grid-cols-2 gap-4">
            <Field label="Amount"><span className="font-mono">{formatInr(event.amount)}</span></Field>
            <Field label="Pipeline time"><span className="font-mono">{event.latency_ms != null ? `${event.latency_ms.toFixed(2)} ms` : '–'}</span></Field>
            <Field label="AI advisory">{event.ai_provider === 'UNAVAILABLE' ? 'No provider, policy only' : event.ai_provider ?? '–'}</Field>
            <Field label="Received"><span className="font-mono text-xs">{new Date(event.ts).toLocaleString()}</span></Field>
            <Field label="Event ID"><code className="font-mono text-xs">{event.event_id ?? '–'}</code></Field>
            <Field label="Correlation ID"><code className="font-mono text-xs">{event.correlation_id ?? '–'}</code></Field>
          </dl>

          {event.audit_id && (
            <Link
              to={`/ledger?id=${encodeURIComponent(event.audit_id)}`}
              className="inline-block text-sm font-medium text-ink underline decoration-line-strong underline-offset-4 hover:decoration-ink"
            >
              Open this decision in the audit ledger
            </Link>
          )}
        </div>
      </aside>
    </div>
  );
}
