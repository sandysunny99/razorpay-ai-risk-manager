import { ReactNode } from 'react';

export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <section className={cx('rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm', className)}>{children}</section>
  );
}

export function CardHeader({ title, subtitle, action }: { title: ReactNode; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-800 px-5 py-4">
      <div className="min-w-0">
        <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
        {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function PageHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">{title}</h1>
        {description && <p className="mt-1 max-w-2xl text-sm text-slate-400">{description}</p>}
      </div>
      {action}
    </div>
  );
}

const DECISION_STYLES: Record<string, string> = {
  ALLOW: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30',
  REVIEW: 'bg-amber-500/15 text-amber-300 ring-amber-500/30',
  BLOCK: 'bg-rose-500/15 text-rose-300 ring-rose-500/30',
  QUARANTINE: 'bg-fuchsia-500/15 text-fuchsia-300 ring-fuchsia-500/30',
};

const LEVEL_STYLES: Record<string, string> = {
  LOW: 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/20',
  MEDIUM: 'bg-amber-500/10 text-amber-300 ring-amber-500/20',
  HIGH: 'bg-orange-500/10 text-orange-300 ring-orange-500/20',
  CRITICAL: 'bg-rose-500/10 text-rose-300 ring-rose-500/20',
};

const NEUTRAL = 'bg-slate-500/10 text-slate-300 ring-slate-500/20';

export function Pill({ children, tone = NEUTRAL, className }: { children: ReactNode; tone?: string; className?: string }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ring-1 ring-inset',
        tone,
        className,
      )}
    >
      {children}
    </span>
  );
}

export function DecisionBadge({ decision }: { decision?: string | null }) {
  const d = decision ?? 'UNAVAILABLE';
  return <Pill tone={DECISION_STYLES[d] ?? NEUTRAL}>{d}</Pill>;
}

export function RiskLevelBadge({ level }: { level?: string | null }) {
  const l = level ?? 'N/A';
  return <Pill tone={LEVEL_STYLES[l] ?? NEUTRAL}>{l}</Pill>;
}

export function riskColor(score: number): string {
  if (score >= 80) return '#f43f5e';
  if (score >= 50) return '#f59e0b';
  if (score >= 25) return '#eab308';
  return '#10b981';
}

export function StatCard({
  label,
  value,
  hint,
  icon,
  accent = 'text-indigo-300',
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
  accent?: string;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{label}</p>
        {icon && <span className={accent}>{icon}</span>}
      </div>
      <p className="mt-3 text-3xl font-semibold tabular-nums text-white">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </Card>
  );
}

export function Notice({ tone = 'info', children }: { tone?: 'info' | 'warn' | 'error'; children: ReactNode }) {
  const styles = {
    info: 'border-sky-500/30 bg-sky-500/10 text-sky-200',
    warn: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
    error: 'border-rose-500/30 bg-rose-500/10 text-rose-200',
  }[tone];
  return <div className={cx('rounded-lg border px-4 py-3 text-sm', styles)}>{children}</div>;
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      aria-hidden
      className={cx('inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent', className)}
    />
  );
}

export function shortId(id: string | undefined | null, keep = 10): string {
  if (!id) return '—';
  return id.length > keep * 2 + 1 ? `${id.slice(0, keep)}…${id.slice(-6)}` : id;
}

export function formatTime(epochSeconds: number | undefined | null): string {
  if (!epochSeconds) return '—';
  return new Date(epochSeconds * 1000).toLocaleString();
}
