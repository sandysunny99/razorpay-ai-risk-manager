import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, ShieldCheck } from 'lucide-react';
import { getAudit, listAuditRecords } from '../services/api';
import { AuditRecord, AuditSummaryItem } from '../types/api';
import { getSafeApiError } from '../utils/errors';
import { Card, CardHeader, cx, DecisionBadge, formatTime, Notice, PageHeader, RiskLevelBadge, shortId, Spinner } from '../components/ui';

export default function AuditViewer() {
  const [auditId, setAuditId] = useState('');
  const [record, setRecord] = useState<AuditRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [looking, setLooking] = useState(false);
  const [items, setItems] = useState<AuditSummaryItem[]>([]);
  const [listError, setListError] = useState<string | null>(null);

  const lookup = useCallback(async (id: string) => {
    if (!id.trim()) return;
    setError(null);
    setRecord(null);
    setLooking(true);
    try {
      setRecord(await getAudit(id.trim()));
    } catch (err: unknown) {
      setError(getSafeApiError(err));
    } finally {
      setLooking(false);
    }
  }, []);

  // Deep link from the live console: /ledger?id=<audit_id>
  const [params] = useSearchParams();
  useEffect(() => {
    const id = params.get('id');
    if (id) {
      setAuditId(id);
      lookup(id);
    }
  }, [params, lookup]);

  useEffect(() => {
    listAuditRecords(50)
      .then((r) => setItems(r.items))
      .catch((err) => setListError(getSafeApiError(err)));
  }, []);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    lookup(auditId);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Ledger"
        description="Tenant-isolated, hash-chained decision records. Lookups for another tenant's records return 404."
      />

      <Card>
        <form onSubmit={onSubmit} className="flex flex-col gap-3 p-4 sm:flex-row">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={auditId}
              onChange={(e) => setAuditId(e.target.value)}
              placeholder="Enter Audit ID (e.g. aud_tenant_123_evt_...)"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 py-2 pl-9 pr-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
          <button
            type="submit"
            disabled={looking}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-500 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-400 disabled:opacity-60"
          >
            {looking && <Spinner />} Lookup
          </button>
        </form>
      </Card>

      {error && <Notice tone="error">{error}</Notice>}

      {record && (
        <Card>
          <CardHeader
            title="Audit Record"
            action={
              record.chain_verified === true ? (
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-300">
                  <ShieldCheck className="h-4 w-4" /> CHAIN VERIFIED
                </span>
              ) : (
                <span className="text-xs font-semibold text-slate-400">UNVERIFIED / DATA UNAVAILABLE</span>
              )
            }
          />
          <dl className="grid grid-cols-1 gap-x-6 gap-y-4 p-5 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {[
              ['Audit ID', <code className="break-all text-slate-200">{record.audit_id}</code>],
              ['Event ID', <code className="break-all text-slate-200">{record.event_id}</code>],
              ['Correlation ID', <code className="break-all text-slate-300">{record.correlation_id}</code>],
              ['Decision', <DecisionBadge decision={record.decision} />],
              ['Risk', <span className="flex items-center gap-2"><RiskLevelBadge level={record.risk_level} /><span className="font-mono text-slate-300">{record.risk_score ?? '—'}</span></span>],
              ['Recorded', <span className="text-slate-300">{formatTime(record.timestamp)}</span>],
              ['Reason codes', <span className="break-all font-mono text-xs text-slate-300">{record.reason_codes?.join(', ') || '—'}</span>],
              ['Record hash', <code className="break-all text-xs text-slate-400">{record.record_hash ?? '—'}</code>],
            ].map(([label, value]) => (
              <div key={label as string}>
                <dt className="text-xs font-medium text-slate-500">{label}</dt>
                <dd className="mt-1">{value}</dd>
              </div>
            ))}
          </dl>
          <div className="border-t border-slate-800 px-5 py-3 text-xs text-amber-200/80">
            <strong>Data Policy:</strong> Audit API is designed to expose metadata only; sensitive payment fields are not displayed by this UI.
          </div>
        </Card>
      )}

      <Card>
        <CardHeader title="Recent records" subtitle="Click a row to inspect it" />
        {listError ? (
          <div className="p-5">
            <Notice tone="error">{listError}</Notice>
          </div>
        ) : items.length === 0 ? (
          <p className="px-5 py-10 text-center text-sm text-slate-500">No records yet for this tenant.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left text-[11px] uppercase tracking-wider text-slate-500">
                  <th className="px-5 py-2.5 font-medium">Audit ID</th>
                  <th className="px-5 py-2.5 font-medium">Recorded</th>
                  <th className="px-5 py-2.5 font-medium">Risk</th>
                  <th className="px-5 py-2.5 font-medium">Decision</th>
                  <th className="px-5 py-2.5 font-medium">Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {items.map((it) => (
                  <tr
                    key={it.audit_id}
                    onClick={() => {
                      setAuditId(it.audit_id);
                      lookup(it.audit_id);
                    }}
                    className={cx('cursor-pointer hover:bg-slate-800/30', record?.audit_id === it.audit_id && 'bg-indigo-500/5')}
                  >
                    <td className="whitespace-nowrap px-5 py-3 font-mono text-xs text-slate-300">{shortId(it.audit_id, 14)}</td>
                    <td className="whitespace-nowrap px-5 py-3 text-xs text-slate-400">{formatTime(it.timestamp)}</td>
                    <td className="px-5 py-3">
                      <RiskLevelBadge level={it.risk_level} />
                    </td>
                    <td className="px-5 py-3">
                      <DecisionBadge decision={it.decision} />
                    </td>
                    <td className="px-5 py-3 font-mono text-[11px] text-slate-500">{it.record_hash ? `${it.record_hash.slice(0, 12)}…` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
