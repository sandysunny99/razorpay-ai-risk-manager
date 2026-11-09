import { useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, Ban, CheckCircle2, Gauge, Pause, Play, ShieldAlert, Skull, Timer, Trash2 } from 'lucide-react';
import { useLiveStream, StreamState } from '../hooks/useLiveStream';
import { LiveEvent } from '../types/api';
import { computeMetrics, formatInr, SCENARIO_LABELS, STAGE_LABELS, verdictOf, Verdict } from '../utils/liveMetrics';
import LiveFeed from '../components/LiveFeed';
import EventDrawer from '../components/EventDrawer';
import GeneratorPanel from '../components/GeneratorPanel';
import { ControlBars, DecisionTimeline, RiskHistogram, TimelineLegend } from '../components/LiveCharts';
import { Card, CardHeader, cx, PageHeader, StatCard } from '../components/ui';

type Filter = 'ALL' | Verdict | 'ZOMBIE';

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'ALL', label: 'All' },
  { id: 'ALLOW', label: 'Allowed' },
  { id: 'REVIEW', label: 'Review' },
  { id: 'BLOCK', label: 'Blocked' },
  { id: 'REJECTED', label: 'Attacks' },
  { id: 'ZOMBIE', label: 'Zombie' },
];

function StreamBadge({ state }: { state: StreamState }) {
  const map = {
    live: ['bg-emerald-400', 'text-emerald-300', 'Live'],
    connecting: ['bg-slate-400', 'text-slate-300', 'Connecting'],
    reconnecting: ['bg-amber-400', 'text-amber-300', 'Reconnecting'],
    offline: ['bg-rose-500', 'text-rose-300', 'Offline'],
  } as const;
  const [dot, text, label] = map[state];
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-semibold" data-testid="stream-state">
      <span className="relative flex h-2 w-2">
        {state === 'live' && <span className={cx('absolute inline-flex h-full w-full animate-ping rounded-full opacity-60', dot)} />}
        <span className={cx('relative inline-flex h-2 w-2 rounded-full', dot)} />
      </span>
      <span className={text}>{label}</span>
    </span>
  );
}

function alertText(e: LiveEvent): { title: string; detail: string; tone: string } {
  if (e.outcome === 'REJECTED') {
    return {
      title: SCENARIO_LABELS[e.scenario ?? ''] ?? 'Attack rejected',
      detail: `Stopped at ${STAGE_LABELS[e.rejected_stage ?? 'unknown'] ?? e.rejected_stage} (HTTP ${e.http_status})`,
      tone: 'text-violet-300',
    };
  }
  if (e.zombie) {
    return { title: `Zombie card · ${e.zombie.severity}`, detail: `${e.zombie.impact} → ${e.zombie.recommendation}`, tone: 'text-fuchsia-300' };
  }
  return { title: `Blocked ${formatInr(e.amount)}`, detail: e.risk_factors?.join(', ') || 'Policy block', tone: 'text-rose-300' };
}

export default function LiveOperations() {
  const { events, state, paused, setPaused, held, setHeld, buffered, clear, generator, setGenerator } = useLiveStream();
  const [filter, setFilter] = useState<Filter>('ALL');
  const [selected, setSelected] = useState<LiveEvent | null>(null);
  const [now, setNow] = useState(() => Date.now());

  // Tick so rolling windows (TPS, timeline) advance even when traffic is quiet.
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const metrics = useMemo(() => computeMetrics(events, now), [events, now]);
  const filtered = useMemo(
    () =>
      events.filter((e) => (filter === 'ALL' ? true : filter === 'ZOMBIE' ? Boolean(e.zombie) : verdictOf(e) === filter)).slice(0, 200),
    [events, filter],
  );
  const alerts = useMemo(
    () => events.filter((e) => e.outcome === 'REJECTED' || e.zombie || verdictOf(e) === 'BLOCK').slice(0, 8),
    [events],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Live Operations"
        description="Every payment event streaming through ingress security, deterministic risk, Zombie Card Saver and the policy engine — in real time."
        action={
          <div className="flex items-center gap-2">
            <StreamBadge state={state} />
            <button
              onClick={() => setPaused(!paused)}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800"
            >
              {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
              {paused ? `Resume${buffered ? ` (${buffered})` : ''}` : 'Pause feed'}
            </button>
            <button
              onClick={clear}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 px-2.5 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800"
              aria-label="Clear feed"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Throughput" value={`${metrics.tps}/s`} hint="Last 10 seconds" icon={<Activity className="h-5 w-5" />} accent="text-sky-300" />
        <StatCard
          label="Approval rate"
          value={metrics.approvalRate != null ? `${metrics.approvalRate}%` : '—'}
          hint={`${metrics.decided} decided`}
          icon={<CheckCircle2 className="h-5 w-5" />}
          accent="text-emerald-400"
        />
        <StatCard label="Blocked" value={metrics.block} hint={`${formatInr(metrics.volumeStopped, true)} stopped`} icon={<Ban className="h-5 w-5" />} accent="text-rose-400" />
        <StatCard label="Attacks rejected" value={metrics.rejected} hint="At ingress, pre-analysis" icon={<ShieldAlert className="h-5 w-5" />} accent="text-violet-400" />
        <StatCard label="Zombie cards" value={metrics.zombies} hint="Dead credential reuse" icon={<Skull className="h-5 w-5" />} accent="text-fuchsia-400" />
        <StatCard
          label="Latency p95"
          value={metrics.p95 != null ? `${metrics.p95.toFixed(1)}ms` : '—'}
          hint={metrics.p50 != null ? `p50 ${metrics.p50.toFixed(1)}ms` : 'Pipeline time'}
          icon={<Timer className="h-5 w-5" />}
          accent="text-amber-300"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Decisions per 5 s" subtitle="Rolling 3-minute window" action={<TimelineLegend />} />
          <div className="p-4">
            <DecisionTimeline data={metrics.timeline} />
          </div>
        </Card>
        <GeneratorPanel status={generator} onChange={setGenerator} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Transaction stream"
            subtitle={
              held && buffered
                ? `Holding while you hover · ${buffered} new`
                : `${events.length} events · hover to hold, click to investigate`
            }
            action={
              <div className="flex flex-wrap gap-1" role="tablist" aria-label="Filter">
                {FILTERS.map((f) => (
                  <button
                    key={f.id}
                    role="tab"
                    aria-selected={filter === f.id}
                    onClick={() => setFilter(f.id)}
                    className={cx(
                      'rounded-md px-2 py-1 text-[11px] font-medium',
                      filter === f.id ? 'bg-indigo-500/20 text-indigo-200' : 'text-slate-400 hover:bg-slate-800',
                    )}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            }
          />
          <div onMouseEnter={() => setHeld(true)} onMouseLeave={() => setHeld(false)}>
            <LiveFeed events={filtered} onSelect={setSelected} selectedSeq={selected?.seq} />
          </div>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader
              title={
                <span className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-400" /> Alerts
                </span>
              }
              subtitle="Blocks, zombie cards and rejected attacks"
            />
            {alerts.length === 0 ? (
              <p className="px-5 py-8 text-center text-xs text-slate-500">All quiet.</p>
            ) : (
              <ul className="divide-y divide-slate-800">
                {alerts.map((e) => {
                  const a = alertText(e);
                  return (
                    <li key={e.seq}>
                      <button onClick={() => setSelected(e)} className="w-full px-5 py-3 text-left hover:bg-slate-800/40">
                        <div className="flex items-center justify-between gap-2">
                          <span className={cx('truncate text-sm font-medium', a.tone)}>{a.title}</span>
                          <span className="shrink-0 font-mono text-[10px] text-slate-500">{new Date(e.ts).toLocaleTimeString()}</span>
                        </div>
                        <p className="mt-0.5 truncate text-xs text-slate-400">{a.detail}</p>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>

          <Card>
            <CardHeader title="Attacks by control" subtitle="Which ingress control stopped them" />
            <div className="p-5">
              <ControlBars data={metrics.byStage} />
            </div>
          </Card>

          <Card>
            <CardHeader
              title={
                <span className="flex items-center gap-2">
                  <Gauge className="h-4 w-4 text-slate-400" /> Risk distribution
                </span>
              }
              subtitle="Deterministic score of decided events"
            />
            <div className="p-4">
              <RiskHistogram data={metrics.riskHistogram} />
            </div>
          </Card>
        </div>
      </div>

      <EventDrawer event={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
