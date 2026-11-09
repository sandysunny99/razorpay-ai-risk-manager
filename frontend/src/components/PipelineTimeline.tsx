import { AlertCircle, CheckCircle2, CircleDashed, MinusCircle, XCircle } from 'lucide-react';
import { cx } from './ui';

export type StageId =
  | 'hmac'
  | 'schema'
  | 'tenant'
  | 'pan'
  | 'replay'
  | 'idempotency'
  | 'risk'
  | 'zombie'
  | 'ai'
  | 'policy'
  | 'audit';

/** `fallback` = stage ran but degraded safely (e.g. no live AI provider → deterministic policy only). */
export type StageStatus = 'pending' | 'passed' | 'failed' | 'skipped' | 'fallback';

export interface StageDef {
  id: StageId;
  label: string;
  group: 'Ingress security' | 'Analysis' | 'Decision';
}

/** Order mirrors backend/api/routes/webhooks.py::process_payment_webhook. */
export const PIPELINE: StageDef[] = [
  { id: 'hmac', label: 'HMAC signature', group: 'Ingress security' },
  { id: 'schema', label: 'Strict schema', group: 'Ingress security' },
  { id: 'tenant', label: 'Tenant binding', group: 'Ingress security' },
  { id: 'pan', label: 'Raw PAN guard', group: 'Ingress security' },
  { id: 'replay', label: 'Replay window', group: 'Ingress security' },
  { id: 'idempotency', label: 'Idempotency', group: 'Ingress security' },
  { id: 'risk', label: 'Deterministic risk', group: 'Analysis' },
  { id: 'zombie', label: 'Zombie Card Saver', group: 'Analysis' },
  { id: 'ai', label: 'AI advisory', group: 'Analysis' },
  { id: 'policy', label: 'Policy engine', group: 'Decision' },
  { id: 'audit', label: 'Hash-chained audit', group: 'Decision' },
];

/** Every stage passed (successful run). */
export function allPassed(): Record<StageId, StageStatus> {
  return Object.fromEntries(PIPELINE.map((s) => [s.id, 'passed'])) as Record<StageId, StageStatus>;
}

/** Stages before `failedAt` passed, `failedAt` failed, everything after was never reached. */
export function failedAt(stage: StageId): Record<StageId, StageStatus> {
  const idx = PIPELINE.findIndex((s) => s.id === stage);
  return Object.fromEntries(
    PIPELINE.map((s, i) => [s.id, i < idx ? 'passed' : i === idx ? 'failed' : 'skipped']),
  ) as Record<StageId, StageStatus>;
}

const ICONS: Record<StageStatus, JSX.Element> = {
  passed: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  failed: <XCircle className="h-4 w-4 text-rose-400" />,
  skipped: <MinusCircle className="h-4 w-4 text-slate-600" />,
  pending: <CircleDashed className="h-4 w-4 animate-spin text-slate-500" />,
  fallback: <AlertCircle className="h-4 w-4 text-amber-400" />,
};

export default function PipelineTimeline({ status }: { status: Record<StageId, StageStatus> }) {
  return (
    <ol className="grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2 lg:grid-cols-1" aria-label="Processing pipeline">
      {PIPELINE.map((stage, i) => {
        const st = status[stage.id];
        const newGroup = i === 0 || PIPELINE[i - 1].group !== stage.group;
        return (
          <li key={stage.id} className="contents">
            {newGroup && (
              <p className="col-span-full mt-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500 first:mt-0">
                {stage.group}
              </p>
            )}
            <div
              data-testid={`stage-${stage.id}`}
              data-status={st}
              className={cx(
                'flex items-center justify-between rounded-md px-2.5 py-1.5 text-sm',
                st === 'failed' && 'bg-rose-500/10 ring-1 ring-inset ring-rose-500/30',
              )}
            >
              <span className={cx('flex items-center gap-2', st === 'skipped' ? 'text-slate-500' : 'text-slate-200')}>
                {ICONS[st]}
                {stage.label}
              </span>
              <span
                className={cx(
                  'text-[10px] font-semibold uppercase tracking-wider',
                  st === 'passed' && 'text-emerald-400',
                  st === 'failed' && 'text-rose-400',
                  st === 'skipped' && 'text-slate-600',
                  st === 'pending' && 'text-slate-500',
                  st === 'fallback' && 'text-amber-400',
                )}
              >
                {{ passed: 'Verified', failed: 'Blocked', skipped: 'Not reached', pending: 'Running', fallback: 'Fail-safe' }[st]}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
