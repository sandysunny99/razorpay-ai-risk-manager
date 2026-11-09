import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { LiveMetrics } from '../utils/liveMetrics';

const SERIES = [
  { key: 'ALLOW', color: '#10b981', label: 'Allowed' },
  { key: 'REVIEW', color: '#f59e0b', label: 'Review' },
  { key: 'BLOCK', color: '#f43f5e', label: 'Blocked' },
  { key: 'REJECTED', color: '#a855f7', label: 'Attack rejected' },
] as const;

const tooltipStyle = {
  contentStyle: { background: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12 },
  labelStyle: { color: '#94a3b8' },
  itemStyle: { color: '#e2e8f0' },
};

export function DecisionTimeline({ data }: { data: LiveMetrics['timeline'] }) {
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
          <defs>
            {SERIES.map((s) => (
              <linearGradient key={s.key} id={`g-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={s.color} stopOpacity={0.55} />
                <stop offset="100%" stopColor={s.color} stopOpacity={0.05} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid stroke="#1e293b" vertical={false} />
          <XAxis dataKey="t" tick={{ fill: '#64748b', fontSize: 10 }} interval={5} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip {...tooltipStyle} />
          {SERIES.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stackId="1"
              stroke={s.color}
              strokeWidth={1.5}
              fill={`url(#g-${s.key})`}
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
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-400">
      {SERIES.map((s) => (
        <li key={s.key} className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
          {s.label}
        </li>
      ))}
    </ul>
  );
}

const histColor = (bucket: number) => (bucket >= 70 ? '#f43f5e' : bucket >= 30 ? '#f59e0b' : '#10b981');

export function RiskHistogram({ data }: { data: LiveMetrics['riskHistogram'] }) {
  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 4, left: -28, bottom: 0 }}>
          <CartesianGrid stroke="#1e293b" vertical={false} />
          <XAxis dataKey="bucket" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis allowDecimals={false} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip {...tooltipStyle} cursor={{ fill: 'rgba(148,163,184,0.08)' }} labelFormatter={(l) => `Risk ${l}–${Number(l) + 9}`} />
          <Bar dataKey="count" name="Events" radius={[3, 3, 0, 0]} isAnimationActive={false}>
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
  if (data.length === 0) return <p className="py-6 text-center text-xs text-slate-500">No attacks rejected yet.</p>;
  return (
    <ul className="space-y-2.5">
      {data.map((d) => (
        <li key={d.stage}>
          <div className="mb-1 flex justify-between text-xs">
            <span className="text-slate-300">{d.label}</span>
            <span className="font-mono tabular-nums text-violet-300">{d.count}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
            <div className="h-full rounded-full bg-violet-500" style={{ width: `${(d.count / max) * 100}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}
