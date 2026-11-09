import { useEffect, useState } from 'react';
import { CreditCard } from 'lucide-react';
import { API_BASE_URL, getRazorpayStatus } from '../services/api';
import { RazorpayStatus } from '../types/api';
import { getSafeApiError } from '../utils/errors';
import { Card, CardHeader, Notice, Pill } from './ui';

export default function RazorpayCard() {
  const [status, setStatus] = useState<RazorpayStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = () =>
      getRazorpayStatus()
        .then((s) => {
          setStatus(s);
          setError(null);
        })
        .catch((err) => setError(getSafeApiError(err)));
    load();
    const id = window.setInterval(load, 10000);
    return () => window.clearInterval(id);
  }, []);

  const origin = API_BASE_URL || window.location.origin;

  return (
    <Card>
      <CardHeader
        title={
          <span className="flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-sky-400" /> Razorpay (test mode)
          </span>
        }
        subtitle="Real payment webhooks, verified with X-Razorpay-Signature"
        action={
          status && (
            <Pill
              tone={
                status.configured
                  ? 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-300 ring-amber-500/20'
              }
            >
              {status.configured ? 'Connected' : 'Not configured'}
            </Pill>
          )
        }
      />
      <div className="space-y-4 p-5 text-sm">
        {error && <Notice tone="error">{error}</Notice>}
        {status && (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ['Received', status.received],
                ['Verified', status.verified],
                ['Bad signature', status.rejected_signature],
                ['Ignored', status.ignored],
              ].map(([label, value]) => (
                <div key={label} className="rounded-lg bg-slate-950/60 p-3">
                  <p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p>
                  <p className="mt-1 font-mono text-lg text-slate-100">{value}</p>
                </div>
              ))}
            </div>
            <ol className="list-decimal space-y-1.5 pl-5 text-slate-300">
              <li>
                Set <code className="text-sky-300">RAZORPAY_WEBHOOK_SECRET</code> on the API (and optionally{' '}
                <code className="text-sky-300">RAZORPAY_TENANT_ID</code>, currently <code>{status.tenant_id}</code>).
              </li>
              <li>
                In the Razorpay Dashboard (Test Mode) → Settings → Webhooks, add:
                <code className="mt-1 block break-all rounded bg-slate-950 px-2 py-1 text-xs text-slate-200">
                  {origin}
                  {status.webhook_path}
                </code>
                <span className="text-xs text-slate-500">Expose localhost with a tunnel (e.g. ngrok / cloudflared) during development.</span>
              </li>
              <li>
                Subscribe to <span className="font-mono text-xs">{status.supported_events.join(', ')}</span> and make a test payment —
                it appears on Live Operations instantly.
              </li>
            </ol>
            <p className="text-xs text-slate-500">
              Card details, e-mail and phone are dropped at the adapter; customers are pseudonymized before analysis.
            </p>
          </>
        )}
      </div>
    </Card>
  );
}
