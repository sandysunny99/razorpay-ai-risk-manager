import { ReactNode } from 'react';

export { EMPTY } from '../utils/liveMetrics';

export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

/** Flat container. Elevation is reserved for overlays (drawer, palette), so panels carry no shadow. */
export function Panel({ children, className, as: Tag = 'section' }: { children: ReactNode; className?: string; as?: 'section' | 'div' }) {
  return <Tag className={cx('rounded-md border border-line bg-surface', className)}>{children}</Tag>;
}

export function PanelHeader({ title, subtitle, action }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line px-4 py-3">
      <div className="min-w-0">
        <h2 className="text-sm font-semibold text-ink">{title}</h2>
        {subtitle && <p className="mt-0.5 text-xs text-ink-subtle">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function PageHeader({ title, description, action }: { title: string; description?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold text-ink">{title}</h1>
        {description && <p className="mt-1 max-w-3xl text-sm text-ink-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

type Tone = 'allow' | 'review' | 'block' | 'zombie' | 'neutral';

const TONE: Record<Tone, string> = {
  allow: 'text-allow border-allow/40 bg-allow/10',
  review: 'text-review border-review/40 bg-review/10',
  block: 'text-block border-block/40 bg-block/10',
  zombie: 'text-zombie border-zombie/40 bg-zombie/10',
  neutral: 'text-ink-muted border-line-strong bg-raised',
};

/** Tags only ever mark a real state (anti-slop R-09): decision, risk level, source health. */
export function Tag({ children, tone = 'neutral', className, outline }: { children: ReactNode; tone?: Tone; className?: string; outline?: boolean }) {
  return (
    <span
      className={cx(
        'inline-flex items-center whitespace-nowrap rounded-sm border px-1.5 py-px text-[11px] font-medium',
        TONE[tone],
        outline && 'bg-transparent',
        className,
      )}
    >
      {children}
    </span>
  );
}

export function decisionTone(decision?: string | null): Tone {
  if (decision === 'ALLOW') return 'allow';
  if (decision === 'REVIEW') return 'review';
  if (decision === 'BLOCK' || decision === 'QUARANTINE') return 'block';
  return 'neutral';
}

export function DecisionTag({ decision }: { decision?: string | null }) {
  return <Tag tone={decisionTone(decision)}>{decision ? decision.charAt(0) + decision.slice(1).toLowerCase() : 'Unavailable'}</Tag>;
}

export function RiskLevelTag({ level }: { level?: string | null }) {
  const tone: Tone = level === 'LOW' ? 'allow' : level === 'MEDIUM' ? 'review' : level === 'HIGH' || level === 'CRITICAL' ? 'block' : 'neutral';
  return <Tag tone={tone}>{level ? level.charAt(0) + level.slice(1).toLowerCase() : 'n/a'}</Tag>;
}

export function riskColor(score: number): string {
  if (score >= 70) return '#f0705f';
  if (score >= 30) return '#e2a945';
  return '#6cc58f';
}

export function Notice({ tone = 'info', children, title }: { tone?: 'info' | 'warn' | 'error'; children: ReactNode; title?: string }) {
  const styles = {
    info: 'border-line-strong bg-raised text-ink-muted',
    warn: 'border-review/40 bg-review/10 text-ink',
    error: 'border-block/40 bg-block/10 text-ink',
  }[tone];
  return (
    <div className={cx('rounded border px-3.5 py-2.5 text-sm', styles)} role={tone === 'error' ? 'alert' : undefined}>
      {title && <p className="font-semibold">{title}</p>}
      <div className={title ? 'mt-0.5' : undefined}>{children}</div>
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <span aria-hidden className={cx('inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent', className)} />;
}

export function shortId(id: string | undefined | null, keep = 10): string {
  if (!id) return '–';
  return id.length > keep * 2 + 1 ? `${id.slice(0, keep)}…${id.slice(-6)}` : id;
}

export function formatTime(epochSeconds: number | undefined | null): string {
  if (!epochSeconds) return '–';
  return new Date(epochSeconds * 1000).toLocaleString();
}
