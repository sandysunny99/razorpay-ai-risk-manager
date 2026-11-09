import { useEffect, useState } from 'react';
import { Pause, Play, Radio } from 'lucide-react';
import { updateGenerator } from '../services/api';
import { GeneratorStatus } from '../types/api';
import { getErrorStatus, getSafeApiError } from '../utils/errors';
import { Card, CardHeader, cx, Notice, Spinner } from './ui';

function Slider({
  label, value, min, max, step, format, onCommit,
}: {
  label: string; value: number; min: number; max: number; step: number;
  format: (v: number) => string; onCommit: (v: number) => void;
}) {
  const [local, setLocal] = useState(value);
  useEffect(() => setLocal(value), [value]);
  return (
    <label className="block">
      <span className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono text-slate-200">{format(local)}</span>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={local}
        onChange={(e) => setLocal(Number(e.target.value))}
        onMouseUp={() => onCommit(local)}
        onTouchEnd={() => onCommit(local)}
        onKeyUp={() => onCommit(local)}
        className="mt-1.5 w-full accent-indigo-500"
      />
    </label>
  );
}

export default function GeneratorPanel({
  status,
  onChange,
}: {
  status: GeneratorStatus | null;
  onChange: (s: GeneratorStatus) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [disabled, setDisabled] = useState(false);

  const apply = async (update: Parameters<typeof updateGenerator>[0]) => {
    setBusy(true);
    setError(null);
    try {
      onChange(await updateGenerator(update));
    } catch (err) {
      if (getErrorStatus(err) === 404) setDisabled(true);
      else setError(getSafeApiError(err));
    } finally {
      setBusy(false);
    }
  };

  const running = status?.running ?? false;

  return (
    <Card>
      <CardHeader
        title={
          <span className="flex items-center gap-2">
            <Radio className={cx('h-4 w-4', running ? 'text-emerald-400' : 'text-slate-500')} /> Synthetic traffic
          </span>
        }
        subtitle="Signed events through the real pipeline"
        action={
          <button
            onClick={() => apply({ running: !running })}
            disabled={busy || disabled}
            className={cx(
              'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition disabled:opacity-50',
              running ? 'bg-slate-800 text-slate-200 hover:bg-slate-700' : 'bg-emerald-500 text-white hover:bg-emerald-400',
            )}
          >
            {busy ? <Spinner className="h-3 w-3" /> : running ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            {running ? 'Stop' : 'Start'}
          </button>
        }
      />
      <div className="space-y-4 p-5">
        {disabled ? (
          <Notice tone="warn">
            Generator disabled. Run the API with <code>NETVRIO_DEMO_MODE=true</code> to stream synthetic traffic. Real Razorpay
            test-mode webhooks still stream live.
          </Notice>
        ) : (
          <>
            <Slider
              label="Throughput"
              value={status?.rate_per_sec ?? 2}
              min={0.5}
              max={15}
              step={0.5}
              format={(v) => `${v}/s`}
              onCommit={(v) => apply({ rate_per_sec: v })}
            />
            <Slider
              label="Attack share"
              value={status?.attack_ratio ?? 0.12}
              min={0}
              max={0.6}
              step={0.02}
              format={(v) => `${Math.round(v * 100)}%`}
              onCommit={(v) => apply({ attack_ratio: v })}
            />
            <Slider
              label="Risky-but-legit share"
              value={status?.risky_ratio ?? 0.2}
              min={0}
              max={0.8}
              step={0.05}
              format={(v) => `${Math.round(v * 100)}%`}
              onCommit={(v) => apply({ risky_ratio: v })}
            />
            <p className="text-[11px] text-slate-500">
              Emitted this run: <span className="font-mono text-slate-300">{status?.emitted ?? 0}</span>
            </p>
          </>
        )}
        {error && <Notice tone="error">{error}</Notice>}
      </div>
    </Card>
  );
}
