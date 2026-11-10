import { ReactNode, useEffect, useState } from 'react';
import { API_BASE_URL, getHealth, getProviderHealth, getRazorpayStatus, getYoupiStatus } from '../services/api';
import { GatewayStatus, ProviderHealth } from '../types/api';
import { useLive } from '../hooks/LiveContext';
import { getSafeApiError } from '../utils/errors';
import { TrafficSettings } from '../components/TrafficControls';
import ComponentsPanel from '../components/ComponentsPanel';
import AiProvidersPanel from '../components/AiProvidersPanel';
import { formatTime, Notice, PageHeader, Panel, PanelHeader, Spinner, Tag } from '../components/ui';

function Row({ name, role, status, tone }: { name: string; role: string; status: string; tone: 'allow' | 'review' | 'block' | 'neutral' }) {
  return (
    <li className="flex items-center justify-between gap-4 px-4 py-3">
      <div>
        <p className="text-sm text-ink">{name}</p>
        <p className="text-xs text-ink-subtle">{role}</p>
      </div>
      <Tag tone={tone}>{status}</Tag>
    </li>
  );
}

function GatewayPanel({
  title, subtitle, load, setup, footnote,
}: {
  title: string; subtitle: string; load: () => Promise<GatewayStatus>; setup: (s: GatewayStatus, origin: string) => ReactNode; footnote: string;
}) {
  const [status, setStatus] = useState<GatewayStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const tick = () => load().then((s) => { setStatus(s); setError(null); }).catch((e) => setError(getSafeApiError(e)));
    tick();
    const id = window.setInterval(tick, 10000);
    return () => window.clearInterval(id);
  }, [load]);
  const origin = API_BASE_URL || window.location.origin;

  return (
    <Panel>
      <PanelHeader
        title={title}
        subtitle={subtitle}
        action={status && <Tag tone={status.configured ? 'allow' : 'review'}>{status.configured ? 'Secret set' : 'Not configured'}</Tag>}
      />
      <div className="space-y-4 p-4 text-sm">
        {error && <Notice tone="error">{error}</Notice>}
        {!status && !error && <p className="text-ink-subtle">Loading.</p>}
        {status && (
          <>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-4">
              {[
                ['Received', status.received],
                ['Verified', status.verified],
                ['Bad signature', status.rejected_signature],
                [status.duplicates !== undefined ? 'Duplicates' : 'Ignored', status.duplicates ?? status.ignored],
              ].map(([label, value]) => (
                <div key={label as string}>
                  <dt className="text-xs text-ink-subtle">{label}</dt>
                  <dd className="font-mono text-lg text-ink">{value}</dd>
                </div>
              ))}
            </dl>
            <p className="text-xs text-ink-subtle">Last delivery: {status.last_event_at ? formatTime(status.last_event_at) : 'none yet'}</p>
            {setup(status, origin)}
            <p className="text-xs text-ink-subtle">{footnote}</p>
          </>
        )}
      </div>
    </Panel>
  );
}

const loadRazorpay = () => getRazorpayStatus() as Promise<GatewayStatus>;

export default function SystemHealth() {
  const { generator, setGenerator, state } = useLive();
  const [health, setHealth] = useState<ProviderHealth | null>(null);
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProviderHealth()
      .then(setHealth)
      .catch((err) => setError(getSafeApiError(err)));
    getHealth().then(() => setApiOk(true)).catch(() => setApiOk(false));
  }, []);

  return (
    <div className="space-y-5">
      <PageHeader
        title="Integrations"
        description="Where payment events come from, and the honest status of each dependency. Anything not exercised against a live service is labelled that way."
      />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <GatewayPanel
          title="YouPI-PG (UPI, primary source)"
          subtitle="Self-hosted UPI gateway. Verified with X-Gateway-Signature and the timestamp-bound V2 signature."
          load={getYoupiStatus}
          footnote="YouPI marks bank-alert payments as OBSERVED_SUCCESS. They are shown as unreconciled: only RECONCILED events are settlement proof. The project is not NPCI or bank approved."
          setup={(s, origin) => (
            <ol className="list-decimal space-y-1 pl-5 text-ink-muted">
              <li>Set <code className="font-mono text-ink">YOUPI_WEBHOOK_SECRET</code> (and <code className="font-mono">YOUPI_REQUIRE_V2=true</code> to insist on V2).</li>
              <li>Point the YouPI merchant webhook at <code className="break-all font-mono text-ink">{origin}{s.webhook_path}</code></li>
              <li>Retries reuse the delivery ID and are acknowledged as duplicates, not reprocessed.</li>
            </ol>
          )}
        />
        <GatewayPanel
          title="Razorpay (test mode, optional)"
          subtitle="Card and UPI payments. Verified with X-Razorpay-Signature."
          load={loadRazorpay}
          footnote="Card details, e-mail and phone are dropped at the adapter; customers are pseudonymised before analysis."
          setup={(s, origin) => (
            <ol className="list-decimal space-y-1 pl-5 text-ink-muted">
              <li>Set <code className="font-mono text-ink">RAZORPAY_WEBHOOK_SECRET</code> on the API (tenant <code className="font-mono">{s.tenant_id}</code>).</li>
              <li>Razorpay Dashboard, Test Mode, Settings, Webhooks: add <code className="break-all font-mono text-ink">{origin}{s.webhook_path}</code></li>
              <li>Subscribe to <span className="font-mono text-xs">{s.supported_events.join(', ')}</span> and make a test payment.</li>
            </ol>
          )}
        />
      </div>

      <Panel>
        <PanelHeader title="Synthetic traffic" subtitle="Signed test events through the real pipeline, for demos and load. Labelled 'Synthetic' in the stream." />
        <div className="p-4">
          <TrafficSettings status={generator} onChange={setGenerator} />
        </div>
      </Panel>

      <ComponentsPanel />

      {error ? (
        <div data-testid="error-message">
          <Notice tone="error" title="Could not load provider status">{error}</Notice>
        </div>
      ) : health ? (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <AiProvidersPanel health={health} onChange={setHealth} />
          <Panel>
            <PanelHeader title="Platform" subtitle="Status measured from this browser session" />
            <ul className="divide-y divide-line">
              <Row name="API" role="GET /health" status={apiOk === null ? 'Checking' : apiOk ? 'Responding' : 'Not responding'} tone={apiOk ? 'allow' : apiOk === false ? 'block' : 'neutral'} />
              <Row name="Event stream" role="Server-Sent Events" status={state === 'live' ? 'Connected' : state === 'offline' ? 'Offline' : 'Connecting'} tone={state === 'live' ? 'allow' : state === 'offline' ? 'block' : 'review'} />
              <Row name="Production authentication" role="JWT or API keys" status="NOT CONNECTED" tone="review" />
              <Row name="Database" role="Audit ledger store" status="SQLite / DEMONSTRATION" tone="neutral" />
            </ul>
          </Panel>
        </div>
      ) : (
        <Panel>
          <div className="flex items-center gap-3 p-4 text-sm text-ink-muted">
            <Spinner /> Loading system status...
          </div>
        </Panel>
      )}
    </div>
  );
}
