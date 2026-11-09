import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getAudit, listAuditRecords, verifyLedgerFull } from '../services/api';
import { AuditRecord, AuditSummaryItem } from '../types/api';
import { getSafeApiError } from '../utils/errors';
import PlateButton from '../components/PlateButton';
import { cx, DecisionTag, formatTime, Notice, PageHeader, Panel, PanelHeader, RiskLevelTag, shortId, Spinner, Tag } from '../components/ui';

export default function AuditViewer() {
  const [auditId, setAuditId] = useState('');
  const [record, setRecord] = useState<AuditRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [looking, setLooking] = useState(false);
  const [items, setItems] = useState<AuditSummaryItem[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [fullResult, setFullResult] = useState<boolean | null>(null);

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

  const loadList = useCallback(() => {
    listAuditRecords(50)
      .then((r) => {
        setItems(r.items);
        setListError(null);
      })
      .catch((err) => setListError(getSafeApiError(err)));
  }, []);
  useEffect(loadList, [loadList]);

  const verifyAll = async () => {
    setVerifying(true);
    try {
      setFullResult((await verifyLedgerFull()).chain_verified);
    } catch (err) {
      setListError(getSafeApiError(err));
    } finally {
      setVerifying(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    lookup(auditId);
  };

  const open = (id: string) => {
    setAuditId(id);
    lookup(id);
  };

  return (
    <div className="space-y-5">
      <PageHeader
        title="Audit ledger"
        description="Every decision and analyst resolution is appended to a SHA-256 hash chain. Records belong to one tenant; another tenant's IDs return not found."
        action={
          <PlateButton variant="quiet" onClick={verifyAll} disabled={verifying}>
            {verifying && <Spinner className="h-3 w-3" />} Verify the whole chain
          </PlateButton>
        }
      />
      {fullResult !== null && (
        <Notice tone={fullResult ? 'info' : 'error'} title={fullResult ? 'Full chain verified' : 'Hash chain broken'}>
          {fullResult
            ? 'Every record was re-hashed from the first entry and each link matches.'
            : 'At least one record no longer matches its hash. Treat the ledger as tampered and investigate.'}
        </Notice>
      )}

      <Panel>
        <form onSubmit={onSubmit} className="flex flex-col gap-3 p-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label htmlFor="audit-id" className="text-sm text-ink">Audit ID</label>
            <input
              id="audit-id"
              type="text"
              value={auditId}
              onChange={(e) => setAuditId(e.target.value)}
              placeholder="aud_tenant_123_evt_..."
              className="mt-1 w-full rounded border border-line-strong bg-canvas px-3 py-2 font-mono text-sm text-ink placeholder:text-ink-subtle focus:border-ink focus:outline-none"
            />
          </div>
          <PlateButton type="submit" disabled={looking || !auditId.trim()}>
            {looking && <Spinner className="h-3 w-3" />} Look up record
          </PlateButton>
        </form>
      </Panel>

      {error && <Notice tone="error" title="Record not available">{error} Check the ID, or that it belongs to this tenant.</Notice>}

      {record && (
        <Panel>
          <PanelHeader
            title="Audit record"
            action={record.chain_verified ? <Tag tone="allow">Chain verified</Tag> : <Tag tone="block">Chain not verified</Tag>}
          />
          <dl className="grid grid-cols-1 gap-x-6 gap-y-4 p-4 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {(
              [
                ['Audit ID', <code className="break-all font-mono text-ink">{record.audit_id}</code>],
                ['Event ID', <code className="break-all font-mono text-ink">{record.event_id}</code>],
                ['Correlation ID', <code className="break-all font-mono text-ink-muted">{record.correlation_id}</code>],
                ['Decision', <DecisionTag decision={record.decision} />],
                [
                  'Risk',
                  <span className="flex items-center gap-2">
                    <RiskLevelTag level={record.risk_level} />
                    <span className="font-mono text-ink-muted">{record.risk_score ?? '–'}</span>
                  </span>,
                ],
                ['Recorded', <span className="font-mono text-ink-muted">{formatTime(record.timestamp)}</span>],
                [
                  'Analyst resolution',
                  record.resolution ? (
                    <span className="text-ink">
                      {record.resolution.action === 'APPROVE' ? 'Approved' : 'Declined'}{' '}
                      <span className="font-mono text-xs text-ink-subtle">{formatTime(record.resolution.timestamp)}</span>
                    </span>
                  ) : (
                    <span className="text-ink-subtle">{record.decision === 'REVIEW' ? 'Waiting for review' : 'Not applicable'}</span>
                  ),
                ],
                ['Reason codes', <span className="break-all font-mono text-xs text-ink-muted">{record.reason_codes?.join(', ') || '–'}</span>],
                ['Record hash', <code className="break-all font-mono text-xs text-ink-subtle">{record.record_hash ?? '–'}</code>],
              ] as [string, React.ReactNode][]
            ).map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs text-ink-subtle">{label}</dt>
                <dd className="mt-1">{value}</dd>
              </div>
            ))}
          </dl>
          <p className="border-t border-line px-4 py-2.5 text-xs text-ink-subtle">
            Data policy: the audit API returns metadata only. Amounts and card references are not stored in the ledger.
          </p>
        </Panel>
      )}

      <Panel>
        <PanelHeader title="Recent decisions" subtitle="Newest first. Select a row to inspect it." />
        {listError ? (
          <div className="p-4">
            <Notice tone="error" title="Could not load the ledger">{listError}</Notice>
          </div>
        ) : items === null ? (
          <p className="px-4 py-8 text-sm text-ink-subtle">Loading records.</p>
        ) : items.length === 0 ? (
          <p className="px-4 py-8 text-sm text-ink-subtle">No decisions recorded for this tenant yet. They appear here once traffic flows.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-xs text-ink-subtle">
                  <th className="px-4 py-2 font-medium">Decision</th>
                  <th className="px-4 py-2 font-medium">Resolution</th>
                  <th className="px-4 py-2 font-medium">Risk</th>
                  <th className="px-4 py-2 font-medium">Audit ID</th>
                  <th className="px-4 py-2 font-medium">Recorded</th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <tr
                    key={it.audit_id}
                    tabIndex={0}
                    onClick={() => open(it.audit_id)}
                    onKeyDown={(e) => e.key === 'Enter' && open(it.audit_id)}
                    className={cx(
                      'cursor-pointer border-b border-line/60 hover:bg-raised focus-visible:bg-raised',
                      record?.audit_id === it.audit_id && 'bg-raised',
                    )}
                  >
                    <td className="px-4 py-2"><DecisionTag decision={it.decision} /></td>
                    <td className="px-4 py-2 text-ink-muted">
                      {it.resolution
                        ? it.resolution.action === 'APPROVE' ? 'Approved' : 'Declined'
                        : it.decision === 'REVIEW' ? <span className="text-review">Waiting</span> : '–'}
                    </td>
                    <td className="px-4 py-2"><RiskLevelTag level={it.risk_level} /></td>
                    <td className="px-4 py-2 font-mono text-xs text-ink-muted">{shortId(it.audit_id, 14)}</td>
                    <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-ink-subtle">{formatTime(it.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
