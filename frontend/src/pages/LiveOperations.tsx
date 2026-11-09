import { useEffect, useMemo, useState } from 'react';
import { Pause, Play } from 'lucide-react';
import { useLive } from '../hooks/LiveContext';
import { StreamState } from '../hooks/useLiveStream';
import { LiveEvent } from '../types/api';
import { computeMetrics, pendingReviews, resolutionsFrom, trafficEvents, verdictOf, Verdict } from '../utils/liveMetrics';
import LiveFeed from '../components/LiveFeed';
import EventDrawer from '../components/EventDrawer';
import ReviewQueue from '../components/ReviewQueue';
import { TrafficToggle } from '../components/TrafficControls';
import { ControlBars, DecisionTimeline, RiskHistogram, TimelineLegend } from '../components/LiveCharts';
import { cx, PageHeader, Panel, PanelHeader } from '../components/ui';

type Filter = 'ALL' | Verdict | 'ZOMBIE' | 'INTEL';

const FILTERS: { id: Filter; label: string }[] = [
  { id: 'ALL', label: 'All' },
  { id: 'BLOCK', label: 'Blocked' },
  { id: 'REVIEW', label: 'Review' },
  { id: 'REJECTED', label: 'Rejected at ingress' },
  { id: 'ZOMBIE', label: 'Zombie cards' },
  { id: 'INTEL', label: 'Threat intel' },
  { id: 'ALLOW', label: 'Allowed' },
];

const STREAM_TEXT: Record<StreamState, { text: string; tone: string }> = {
  live: { text: 'Stream connected', tone: 'text-allow' },
  connecting: { text: 'Connecting to stream', tone: 'text-ink-muted' },
  reconnecting: { text: 'Stream lost, retrying every 3 s', tone: 'text-review' },
  offline: { text: 'Stream offline. Check that the API is running.', tone: 'text-block' },
};

function matches(e: LiveEvent, f: Filter): boolean {
  if (f === 'ALL') return true;
  if (f === 'ZOMBIE') return Boolean(e.zombie);
  if (f === 'INTEL') return Boolean(e.threat?.length);
  return verdictOf(e) === f;
}

function Figure({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className="min-w-[96px] px-4 py-2">
      <p className="text-xs text-ink-subtle">{label}</p>
      <p className={cx('font-mono text-lg tabular-nums', tone ?? 'text-ink')}>{value}</p>
    </div>
  );
}

export default function LiveOperations() {
  const live = useLive();
  const { events, state, paused, setPaused, held, setHeld, buffered, generator, setGenerator, localResolved, markResolved } = live;
  const [filter, setFilter] = useState<Filter>('ALL');
  const [selected, setSelected] = useState<LiveEvent | null>(null);
  const [now, setNow] = useState(() => Date.now());

  // Tick so rolling windows (rate, timeline) advance even when traffic is quiet.
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const traffic = useMemo(() => trafficEvents(events), [events]);
  const metrics = useMemo(() => computeMetrics(events, now), [events, now]);
  const resolved = useMemo(() => {
    const m = resolutionsFrom(events);
    localResolved.forEach((v, k) => m.set(k, v));
    return m;
  }, [events, localResolved]);
  const queue = useMemo(() => pendingReviews(traffic, resolved).slice(0, 50), [traffic, resolved]);
  const filtered = useMemo(() => traffic.filter((e) => matches(e, filter)).slice(0, 200), [traffic, filter]);
  const stream = STREAM_TEXT[state];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Live operations"
        description="Every payment event in real time, from ingress checks to the policy decision. Work the review queue on the left; investigate anything in the stream."
        action={<TrafficToggle status={generator} onChange={setGenerator} />}
      />

      <Panel>
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-2.5 text-sm">
          <p className={stream.tone} role="status">
            {stream.text}
            {state === 'live' && <span className="text-ink-muted">. {metrics.tps} events/s over the last 10 s.</span>}
          </p>
          <button
            onClick={() => setPaused(!paused)}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded px-2 py-1 text-sm text-ink-muted hover:bg-raised hover:text-ink"
          >
            {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
            {paused ? `Resume stream${buffered ? ` (${buffered} new)` : ''}` : 'Pause stream'}
          </button>
        </div>
        <div className="flex flex-wrap divide-x divide-line">
          <Figure label="Waiting for review" value={queue.length} tone={queue.length ? 'text-review' : undefined} />
          <Figure label="Blocked" value={metrics.block} tone={metrics.block ? 'text-block' : undefined} />
          <Figure label="Rejected at ingress" value={metrics.rejected} />
          <Figure label="Zombie cards" value={metrics.zombies} tone={metrics.zombies ? 'text-zombie' : undefined} />
          <Figure label="Threat-intel hits" value={metrics.threatHits} />
          <Figure label="Approval rate" value={metrics.approvalRate != null ? `${metrics.approvalRate}%` : '–'} />
          <Figure label="Pipeline p95" value={metrics.p95 != null ? `${metrics.p95.toFixed(1)} ms` : '–'} />
        </div>
      </Panel>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-5">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title={`Needs a decision (${queue.length})`}
            subtitle="Policy sent these to review. Your choice is written to the audit ledger."
          />
          <ReviewQueue items={queue} onOpen={setSelected} onResolved={markResolved} />
        </Panel>

        <Panel className="xl:col-span-3">
          <PanelHeader
            title="Event stream"
            subtitle={
              held && buffered
                ? `Held while your pointer is over the list. ${buffered} new events waiting.`
                : `${traffic.length} events in this session. Hover holds the list still; Enter opens a row.`
            }
          />
          <div className="flex flex-wrap gap-1 border-b border-line px-3 py-2" role="tablist" aria-label="Filter stream">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                role="tab"
                aria-selected={filter === f.id}
                onClick={() => setFilter(f.id)}
                className={cx(
                  'min-h-[36px] cursor-pointer rounded px-2.5 py-1 text-sm',
                  filter === f.id ? 'bg-raised text-ink' : 'text-ink-subtle hover:text-ink',
                )}
              >
                {f.label}
              </button>
            ))}
          </div>
          <div onMouseEnter={() => setHeld(true)} onMouseLeave={() => setHeld(false)}>
            <LiveFeed
              events={filtered}
              onSelect={setSelected}
              selectedSeq={selected?.seq}
              emptyMessage={
                traffic.length === 0
                  ? 'No events yet. Start synthetic traffic or send a Razorpay or YouPI test webhook.'
                  : 'No events match this filter in the current session.'
              }
            />
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader title="Is hostile traffic rising?" subtitle="Outcomes per 5 seconds, last 3 minutes" action={<TimelineLegend />} />
          <div className="p-3">
            <DecisionTimeline data={metrics.timeline} />
          </div>
        </Panel>
        <div className="space-y-5">
          <Panel>
            <PanelHeader title="Which control stopped it?" subtitle="Requests rejected before analysis" />
            <div className="p-4">
              <ControlBars data={metrics.byStage} />
            </div>
          </Panel>
          <Panel>
            <PanelHeader title="How risky is accepted traffic?" subtitle="Deterministic score of decided events" />
            <div className="p-3">
              <RiskHistogram data={metrics.riskHistogram} />
            </div>
          </Panel>
        </div>
      </div>

      <EventDrawer event={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
