import { useState } from 'react';
import { verifyProviders } from '../services/api';
import { ProviderHealth } from '../types/api';
import { getErrorStatus, getSafeApiError } from '../utils/errors';
import PlateButton from './PlateButton';
import { Notice, Panel, PanelHeader, Spinner, Tag } from './ui';

const LABELS: Record<string, string> = {
  cloudflare: 'Cloudflare Workers AI',
  groq: 'Groq',
  gemini: 'Google Gemini',
  nvidia: 'NVIDIA NIM',
  huggingface: 'Hugging Face',
  grok: 'xAI Grok',
};

function tone(status: string) {
  if (status === 'AVAILABLE') return 'allow' as const;
  if (status === 'NOT VERIFIED') return 'review' as const;
  if (status === 'NOT CONFIGURED') return 'neutral' as const;
  return 'block' as const;
}

/** The real fallback chain from GET /health/providers, with an on-demand live check. */
export default function AiProvidersPanel({ health, onChange }: { health: ProviderHealth; onChange: (h: ProviderHealth) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chain = health.chain ?? [];

  const verify = async () => {
    setBusy(true);
    setError(null);
    try {
      onChange(await verifyProviders());
    } catch (err) {
      setError(getErrorStatus(err) === 404 ? 'Live checks are only available in demo mode.' : getSafeApiError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel>
      <PanelHeader
        title="AI advisory providers"
        subtitle="Tried in this order until one answers. Advisory only: the policy engine always decides."
        action={
          <PlateButton size="sm" variant="quiet" onClick={verify} disabled={busy || !chain.some((r) => r.configured)}>
            {busy && <Spinner className="h-3 w-3" />} Verify now
          </PlateButton>
        }
      />
      {chain.length === 0 ? (
        <p className="px-4 py-6 text-sm text-ink-subtle">No providers in NETVRIO_LLM_CHAIN.</p>
      ) : (
        <ol className="divide-y divide-line">
          {chain.map((r, i) => (
            <li key={r.name} className="flex items-start justify-between gap-4 px-4 py-3">
              <div className="min-w-0">
                <p className="text-sm text-ink">
                  <span className="mr-2 font-mono text-xs text-ink-subtle">{i + 1}</span>
                  {LABELS[r.name] ?? r.name}
                </p>
                <p className="truncate font-mono text-xs text-ink-subtle">{r.configured ? r.model : 'No key set'}</p>
                {r.detail && <p className="mt-0.5 text-xs text-block">{r.detail}</p>}
              </div>
              <div className="shrink-0 text-right">
                <Tag tone={tone(r.status)}>{r.status === 'AVAILABLE' ? 'Answering' : r.status}</Tag>
                {r.latency_ms != null && <p className="mt-1 font-mono text-xs text-ink-subtle">{r.latency_ms} ms</p>}
              </div>
            </li>
          ))}
        </ol>
      )}
      <div className="space-y-2 border-t border-line px-4 py-3 text-xs text-ink-subtle">
        {health.scope && (
          <p>
            {health.scope === 'flagged'
              ? 'Only payments that are not plainly safe get an AI note.'
              : 'Every payment gets an AI note.'}
            {health.budget && ` Budget: ${health.budget.used_last_minute} of ${health.budget.limit_per_minute} calls used in the last minute.`}
          </p>
        )}
        <p>Verify sends one synthetic, masked request to each configured provider. Keys never leave the server.</p>
        {error && <Notice tone="error">{error}</Notice>}
      </div>
    </Panel>
  );
}
