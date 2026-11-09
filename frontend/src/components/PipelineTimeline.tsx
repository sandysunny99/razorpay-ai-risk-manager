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
  | 'intel'
  | 'zombie'
  | 'ml'
  | 'ai'
  | 'policy'
  | 'audit';

/** `fallback` = stage ran but degraded safely (e.g. no live AI provider, so policy decides alone). */
export type StageStatus = 'pending' | 'passed' | 'failed' | 'skipped' | 'fallback';

export interface StageDef {
  id: StageId;
  label: string;
  group: 'Ingress security' | 'Analysis' | 'Decision';
}

/** Order mirrors backend/api/routes/webhooks.py::run_pipeline. */
export const PIPELINE: StageDef[] = [
  { id: 'hmac', label: 'HMAC signature', group: 'Ingress security' },
  { id: 'schema', label: 'Strict schema', group: 'Ingress security' },
  { id: 'tenant', label: 'Tenant binding', group: 'Ingress security' },
  { id: 'pan', label: 'Raw PAN guard', group: 'Ingress security' },
  { id: 'replay', label: 'Replay window', group: 'Ingress security' },
  { id: 'idempotency', label: 'Idempotency', group: 'Ingress security' },
  { id: 'risk', label: 'Deterministic risk', group: 'Analysis' },
  { id: 'intel', label: 'Threat intel and exposure', group: 'Analysis' },
  { id: 'zombie', label: 'Zombie Card Saver', group: 'Analysis' },
  { id: 'ml', label: 'ML second opinion', group: 'Analysis' },
  { id: 'ai', label: 'AI advisory', group: 'Analysis' },
  { id: 'policy', label: 'Policy engine', group: 'Decision' },
  { id: 'audit', label: 'Hash-chained audit', group: 'Decision' },
];

export function allPassed(): Record<StageId, StageStatus> {
  return Object.fromEntries(PIPELINE.map((s) => [s.id, 'passed'])) as Record<StageId, StageStatus>;
}

/** Stages before `stage` passed, `stage` failed, everything after was never reached. */
export function failedAt(stage: StageId): Record<StageId, StageStatus> {
  const idx = PIPELINE.findIndex((s) => s.id === stage);
  return Object.fromEntries(
    PIPELINE.map((s, i) => [s.id, i < idx ? 'passed' : i === idx ? 'failed' : 'skipped']),
  ) as Record<StageId, StageStatus>;
}

const ICONS: Record<StageStatus, JSX.Element> = {
  passed: <CheckCircle2 className="h-4 w-4 text-allow" aria-hidden />,
  failed: <XCircle className="h-4 w-4 text-block" aria-hidden />,
  skipped: <MinusCircle className="h-4 w-4 text-ink-subtle" aria-hidden />,
  pending: <CircleDashed className="h-4 w-4 animate-spin text-ink-subtle" aria-hidden />,
  fallback: <AlertCircle className="h-4 w-4 text-review" aria-hidden />,
};

const LABEL: Record<StageStatus, string> = {
  passed: 'Passed',
  failed: 'Stopped here',
  skipped: 'Not reached',
  pending: 'Running',
  fallback: 'Fail-safe',
};

export default function PipelineTimeline({ status }: { status: Record<StageId, StageStatus> }) {
  return (
    <ol className="space-y-px" aria-label="Processing pipeline">
      {PIPELINE.map((stage, i) => {
        const st = status[stage.id];
        const newGroup = i === 0 || PIPELINE[i - 1].group !== stage.group;
        return (
          <li key={stage.id}>
            {newGroup && <p className="mb-1 mt-3 text-xs font-medium text-ink-subtle first:mt-0">{stage.group}</p>}
            <div
              data-testid={`stage-${stage.id}`}
              data-status={st}
              className={cx(
                'flex items-center justify-between gap-3 rounded-sm px-2 py-1.5 text-sm',
                st === 'failed' && 'border-l-2 border-block bg-block/10',
              )}
            >
              <span className={cx('flex items-center gap-2', st === 'skipped' ? 'text-ink-subtle' : 'text-ink')}>
                {ICONS[st]}
                {stage.label}
              </span>
              <span
                className={cx(
                  'text-xs',
                  st === 'failed' ? 'font-medium text-block' : st === 'fallback' ? 'text-review' : 'text-ink-subtle',
                )}
              >
                {LABEL[st]}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
