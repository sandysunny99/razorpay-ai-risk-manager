import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { LiveMetrics } from '../utils/liveMetrics';

// Hostile traffic is drawn as a hatched-looking outline (stroke only) so it never relies on hue
// alone to be told apart from the "blocked" series.
const SERIES = [
  { key: 'ALLOW', color: '#6cc58f', label: 'Allowed', fill: 0.35 },
  { key: 'REVIEW', color: '#e2a945', label: 'Review', fill: 0.35 },
  { key: 'BLOCK', color: '#f0705f', label: 'Blocked', fill: 0.35 },
  { key: 'REJECTED', color: '#ecebe7', label: 'Attack rejected at ingress', fill: 0.06 },
] as const;

const axis = { fill: '#908e88', fontSize: 11, fontFamily: 'IBM Plex Mono, monospace' };
const tooltip = {
  contentStyle: { background: '#1d2024', border: '1px solid #3d424a', borderRadius: 5, fontSize: 12 },
  labelStyle: { color: '#b4b2ac' },
  itemStyle: { color: '#ecebe7' },
};

export function DecisionTimeline({ data }: { data: LiveMetrics['timeline'] }) {
  return (
    <div className="h-52 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
          <CartesianGrid stroke="#2b2f35" vertical={false} />
          <XAxis dataKey="t" tick={axis} interval={5} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} tick={axis} axisLine={false} tickLine={false} />
          <Tooltip {...tooltip} />
          {SERIES.map((s) => (
            <Area
              key={s.key}
              type="stepAfter"
              dataKey={s.key}
              name={s.label}
              stackId="1"
              stroke={s.color}
              strokeWidth={1.5}
              strokeDasharray={s.key === 'REJECTED' ? '4 3' : undefined}
              fill={s.color}
              fillOpacity={s.fill}
              isAnimationActive={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function TimelineLegend() {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-muted">
      {SERIES.map((s) => (
        <li key={s.key} className="flex items-center gap-1.5">
          <span
            className="h-2.5 w-2.5 rounded-sm border"
            style={{ borderColor: s.color, backgroundColor: s.key === 'REJECTED' ? 'transparent' : s.color }}
          />
          {s.label}
        </li>
      ))}
    </ul>
  );
}

const histColor = (bucket: number) => (bucket >= 70 ? '#f0705f' : bucket >= 30 ? '#e2a945' : '#6cc58f');

export function RiskHistogram({ data }: { data: LiveMetrics['riskHistogram'] }) {
  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 4, left: -28, bottom: 0 }}>
          <CartesianGrid stroke="#2b2f35" vertical={false} />
          <XAxis dataKey="bucket" tick={axis} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} tick={axis} axisLine={false} tickLine={false} />
          <Tooltip {...tooltip} cursor={{ fill: 'rgba(236,235,231,0.05)' }} labelFormatter={(l) => `Score ${l} to ${Number(l) + 9}`} />
          <Bar dataKey="count" name="Events" isAnimationActive={false}>
            {data.map((d) => (
              <Cell key={d.bucket} fill={histColor(Number(d.bucket))} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ControlBars({ data }: { data: LiveMetrics['byStage'] }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  if (data.length === 0) return <p className="py-4 text-sm text-ink-subtle">No hostile requests yet in this buffer.</p>;
  return (
    <ul className="space-y-2.5">
      {data.map((d) => (
        <li key={d.stage}>
          <div className="mb-1 flex justify-between text-sm">
            <span className="text-ink-muted">{d.label}</span>
            <span className="font-mono tabular-nums text-ink">{d.count}</span>
          </div>
          <div className="h-1.5 bg-raised">
            <div className="h-full bg-ink-muted" style={{ width: `${(d.count / max) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}
