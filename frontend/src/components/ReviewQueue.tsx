import { useState } from 'react';
import { resolveReview } from '../services/api';
import { LiveEvent } from '../types/api';
import { getErrorStatus, getSafeApiError } from '../utils/errors';
import { eventLabel, formatInr } from '../utils/liveMetrics';
import PlateButton from './PlateButton';
import { signalText } from './LiveFeed';
import { cx, Notice } from './ui';

/**
 * The screen's focal point: REVIEW decisions waiting for a human. Approve / Decline write a
 * hash-chained resolution record (POST /audit/{id}/resolution) and broadcast it, so every open
 * console drops the item at the same time.
 */
export default function ReviewQueue({
  items,
  onOpen,
  onResolved,
}: {
  items: LiveEvent[];
  onOpen: (e: LiveEvent) => void;
  onResolved: (auditId: string, action: 'APPROVE' | 'DECLINE') => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const act = async (e: LiveEvent, action: 'APPROVE' | 'DECLINE') => {
    if (!e.audit_id) return;
    setBusy(e.audit_id);
    setError(null);
    try {
      await resolveReview(e.audit_id, action);
      onResolved(e.audit_id, action);
    } catch (err) {
      if (getErrorStatus(err) === 409) onResolved(e.audit_id, action); // someone else resolved it first
      else setError(getSafeApiError(err));
    } finally {
      setBusy(null);
    }
  };

  if (items.length === 0) {
    return (
      <p className="px-4 py-10 text-center text-sm text-ink-subtle">
        Nothing waiting. Payments the policy engine sends to review will appear here.
      </p>
    );
  }

  return (
    <div>
      {error && (
        <div className="px-4 pt-3">
          <Notice tone="error">Could not record the decision: {error}</Notice>
        </div>
      )}
      <ul className="max-h-[560px] divide-y divide-line overflow-auto" aria-label="Payments waiting for review">
        {items.map((e) => {
          const sig = signalText(e);
          const zombie = Boolean(e.zombie) || e.threat?.some((m) => m.category === 'card_exposed');
          return (
            <li key={e.seq} className={cx('px-4 py-3', zombie && 'border-l-2 border-zombie')}>
              <div className="flex items-start justify-between gap-3">
                <button onClick={() => onOpen(e)} className="min-w-0 text-left">
                  <p className="font-mono text-base font-medium tabular-nums text-ink">{formatInr(e.amount)}</p>
                  <p className={cx('mt-0.5 truncate text-sm', sig?.tone ?? 'text-ink-muted')}>{sig?.text ?? eventLabel(e)}</p>
                  <p className="mt-0.5 text-xs text-ink-subtle">
                    {eventLabel(e)} · <span className="font-mono">{new Date(e.ts).toLocaleTimeString()}</span>
                  </p>
                </button>
                <div className="flex shrink-0 gap-2">
                  <PlateButton
                    size="sm"
                    variant="allow"
                    disabled={busy === e.audit_id}
                    onClick={() => act(e, 'APPROVE')}
                    aria-label={`Approve ${formatInr(e.amount)} payment`}
                  >
                    Approve
                  </PlateButton>
                  <PlateButton
                    size="sm"
                    variant="block"
                    disabled={busy === e.audit_id}
                    onClick={() => act(e, 'DECLINE')}
                    aria-label={`Decline ${formatInr(e.amount)} payment`}
                  >
                    Decline
                  </PlateButton>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
