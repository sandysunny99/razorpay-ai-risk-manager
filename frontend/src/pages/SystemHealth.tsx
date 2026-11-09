import { useEffect, useState } from 'react';
import { Bot, Database, KeyRound, Server } from 'lucide-react';
import { getProviderHealth } from '../services/api';
import { ProviderHealth } from '../types/api';
import { getSafeApiError } from '../utils/errors';
import { Card, CardHeader, Notice, PageHeader, Pill, Spinner } from '../components/ui';
import RazorpayCard from '../components/RazorpayCard';

function statusTone(status: string): string {
  if (status === 'HEALTHY') return 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/20';
  if (status === 'DEGRADED' || status.startsWith('NOT VERIFIED')) return 'bg-amber-500/10 text-amber-300 ring-amber-500/20';
  if (status === 'UNAVAILABLE' || status === 'MISCONFIGURED') return 'bg-rose-500/10 text-rose-300 ring-rose-500/20';
  return 'bg-slate-500/10 text-slate-300 ring-slate-500/20';
}

function Row({ icon, name, role, status }: { icon: JSX.Element; name: string; role: string; status: string }) {
  return (
    <li className="flex items-center justify-between gap-4 px-5 py-4">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-800 text-slate-300">{icon}</span>
        <div>
          <p className="text-sm font-medium text-slate-100">{name}</p>
          <p className="text-xs text-slate-500">{role}</p>
        </div>
      </div>
      <Pill tone={statusTone(status)} className="normal-case">
        {status}
      </Pill>
    </li>
  );
}

export default function SystemHealth() {
  const [health, setHealth] = useState<ProviderHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProviderHealth()
      .then(setHealth)
      .catch((err) => setError(getSafeApiError(err)));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Integrations & Health"
        description="Connect real Razorpay test-mode traffic and see honest integration status. Anything not exercised against a live service is labelled as such."
      />

      <RazorpayCard />

      {error ? (
        <div data-testid="error-message">
          <Notice tone="error">{error}</Notice>
        </div>
      ) : health ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader title="AI advisory providers" subtitle="Fallback chain — advisory only, never authoritative" />
            <ul className="divide-y divide-slate-800">
              <Row icon={<Bot className="h-4 w-4" />} name="Cloudflare / Primary" role="Workers AI" status={health.primary} />
              <Row icon={<Bot className="h-4 w-4" />} name="Grok / Secondary" role="xAI" status={health.secondary} />
              <Row icon={<Bot className="h-4 w-4" />} name="Hugging Face / Fallback" role="Inference API" status={health.fallback} />
            </ul>
          </Card>
          <Card>
            <CardHeader title="Platform" subtitle="Demo-grade components" />
            <ul className="divide-y divide-slate-800">
              <Row icon={<Server className="h-4 w-4" />} name="Deterministic security path" role="HMAC · replay · idempotency · policy" status="HEALTHY" />
              <Row icon={<Server className="h-4 w-4" />} name="Real-time stream" role="Server-Sent Events · in-process bus" status="HEALTHY" />
              <Row icon={<KeyRound className="h-4 w-4" />} name="Production Authentication" role="JWT / API keys" status="NOT CONNECTED" />
              <Row icon={<Database className="h-4 w-4" />} name="Database" role="Audit ledger store" status="SQLite / DEMONSTRATION" />
            </ul>
          </Card>
          <div className="lg:col-span-2">
            <Notice tone="info">
              Core deterministic security path is functional. External live integrations are isolated for demonstration.
            </Notice>
          </div>
        </div>
      ) : (
        <Card>
          <div className="flex items-center gap-3 p-5 text-sm text-slate-400">
            <Spinner /> Loading system status...
          </div>
        </Card>
      )}
    </div>
  );
}
