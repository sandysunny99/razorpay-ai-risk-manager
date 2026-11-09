import { useEffect, useState } from 'react';
import { updateGenerator } from '../services/api';
import { GeneratorStatus } from '../types/api';
import { getErrorStatus, getSafeApiError } from '../utils/errors';
import PlateButton from './PlateButton';
import { Notice, Spinner } from './ui';

export function useTrafficActions(onChange: (s: GeneratorStatus) => void) {
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
  return { apply, busy, error, disabled };
}

/** Start/stop button for the synthetic traffic source. */
export function TrafficToggle({ status, onChange }: { status: GeneratorStatus | null; onChange: (s: GeneratorStatus) => void }) {
  const { apply, busy, error, disabled } = useTrafficActions(onChange);
  const running = status?.running ?? false;
  if (disabled || (!status && !busy)) {
    return <span className="text-xs text-ink-subtle">Synthetic traffic off (demo mode disabled)</span>;
  }
  return (
    <span className="inline-flex items-center gap-2">
      <PlateButton size="sm" variant={running ? 'quiet' : 'primary'} onClick={() => apply({ running: !running })} disabled={busy}>
        {busy && <Spinner className="h-3 w-3" />}
        {running ? 'Stop synthetic traffic' : 'Start synthetic traffic'}
      </PlateButton>
      {error && <span className="text-xs text-block">{error}</span>}
    </span>
  );
}

function Slider({
  id, label, hint, value, min, max, step, format, onCommit,
}: {
  id: string; label: string; hint: string; value: number; min: number; max: number; step: number;
  format: (v: number) => string; onCommit: (v: number) => void;
}) {
  const [local, setLocal] = useState(value);
  useEffect(() => setLocal(value), [value]);
  return (
    <div>
      <div className="flex justify-between text-sm">
        <label htmlFor={id} className="text-ink">{label}</label>
        <span className="font-mono text-ink">{format(local)}</span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={local}
        onChange={(e) => setLocal(Number(e.target.value))}
        onPointerUp={() => onCommit(local)}
        onKeyUp={() => onCommit(local)}
        className="mt-2 w-full cursor-pointer accent-[#ecebe7]"
      />
      <p className="mt-1 text-xs text-ink-subtle">{hint}</p>
    </div>
  );
}

/** Full traffic configuration (Integrations page). */
export function TrafficSettings({ status, onChange }: { status: GeneratorStatus | null; onChange: (s: GeneratorStatus) => void }) {
  const { apply, error, disabled } = useTrafficActions(onChange);
  if (disabled || !status) {
    return (
      <Notice tone="info">
        The synthetic source is off. Start the API with <code className="font-mono">NETVRIO_DEMO_MODE=true</code> in a non-production{' '}
        <code className="font-mono">NETVRIO_ENV</code> to enable it. Razorpay and YouPI webhooks stream regardless.
      </Notice>
    );
  }
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-ink-muted">
          {status.running ? 'Running' : 'Stopped'}, <span className="font-mono text-ink">{status.emitted}</span> events sent this run.
        </p>
        <TrafficToggle status={status} onChange={onChange} />
      </div>
      <Slider id="rate" label="Events per second" hint="Arrivals are randomised around this rate." value={status.rate_per_sec}
        min={0.5} max={15} step={0.5} format={(v) => `${v}/s`} onCommit={(v) => apply({ rate_per_sec: v })} />
      <Slider id="attack" label="Hostile share" hint="Forged signatures, replays, duplicates, cross-tenant injection, raw PAN."
        value={status.attack_ratio} min={0} max={0.6} step={0.02} format={(v) => `${Math.round(v * 100)}%`}
        onCommit={(v) => apply({ attack_ratio: v })} />
      <Slider id="risky" label="Risky but legitimate share" hint="High value, bursts, dead tokens, listed IPs."
        value={status.risky_ratio} min={0} max={0.8} step={0.05} format={(v) => `${Math.round(v * 100)}%`}
        onCommit={(v) => apply({ risky_ratio: v })} />
      {error && <Notice tone="error">{error}</Notice>}
    </div>
  );
}
