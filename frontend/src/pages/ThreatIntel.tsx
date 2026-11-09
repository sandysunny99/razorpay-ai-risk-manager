import { useCallback, useEffect, useState } from 'react';
import { getExposureSummary, getIntelMatches, getIntelStatus, refreshIntelFeeds } from '../services/api';
import { ExposureSummary, IntelMatchLog, IntelStatus } from '../types/api';
import { getErrorStatus, getSafeApiError } from '../utils/errors';
import PlateButton from '../components/PlateButton';
import { formatTime, Notice, PageHeader, Panel, PanelHeader, Spinner, Tag } from '../components/ui';

export default function ThreatIntel() {
  const [status, setStatus] = useState<IntelStatus | null>(null);
  const [matches, setMatches] = useState<IntelMatchLog[]>([]);
  const [exposure, setExposure] = useState<ExposureSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [s, m, x] = await Promise.all([getIntelStatus(), getIntelMatches(30), getExposureSummary()]);
      setStatus(s);
      setMatches(m.items);
      setExposure(x);
      setError(null);
    } catch (err) {
      setError(getSafeApiError(err));
    }
  }, []);

  useEffect(() => {
    load();
    const id = window.setInterval(load, 5000);
    return () => window.clearInterval(id);
  }, [load]);

  const refresh = async () => {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const r = await refreshIntelFeeds();
      setStatus(r);
      const parts = Object.entries(r.results).map(([k, v]) => `${k}: ${v < 0 ? 'failed, previous list kept' : `${v} indicators`}`);
      setRefreshMsg(parts.length ? parts.join('. ') : 'Live feeds are off. Set NETVRIO_TI_LIVE_FEEDS=true on the API to download them.');
    } catch (err) {
      setRefreshMsg(getErrorStatus(err) === 404 ? 'Feed refresh is only available in demo mode.' : getSafeApiError(err));
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="space-y-5">
      <PageHeader
        title="Threat intelligence"
        description="Indicators are checked locally inside the pipeline, so lookups add no network calls and send no customer data to third parties. Matches add evidence; the policy engine still decides."
        action={
          <PlateButton onClick={refresh} disabled={refreshing || !status?.live_feeds_enabled}
            title={status?.live_feeds_enabled ? undefined : 'Live feeds are disabled on the API'}>
            {refreshing && <Spinner className="h-3 w-3" />} Refresh live feeds
          </PlateButton>
        }
      />
      {error && <Notice tone="error" title="Could not load threat intelligence">{error}. Check that the API is running.</Notice>}
      {refreshMsg && <Notice>{refreshMsg}</Notice>}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Panel className="xl:col-span-2">
          <PanelHeader
            title="Indicator sources"
            subtitle={status ? `${status.lookups} lookups, ${status.hits} with a match, since the API started` : 'Loading'}
          />
          {status ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-line text-left text-xs text-ink-subtle">
                    <th className="px-4 py-2 font-medium">Source</th>
                    <th className="px-4 py-2 font-medium">State</th>
                    <th className="px-4 py-2 text-right font-medium">Indicators</th>
                    <th className="px-4 py-2 font-medium">Last refresh</th>
                    <th className="px-4 py-2 font-medium">Terms</th>
                  </tr>
                </thead>
                <tbody>
                  {status.sources.map((s) => (
                    <tr key={s.name} className="border-b border-line/60 align-top">
                      <td className="px-4 py-2.5">
                        <p className="text-ink">{s.name}</p>
                        <p className="text-xs text-ink-subtle">{s.category.replace(/_/g, ' ')}, confidence {s.confidence}</p>
                      </td>
                      <td className="px-4 py-2.5">
                        {!s.enabled ? <Tag>Off</Tag> : s.last_error ? <Tag tone="block">Error</Tag> : s.indicators ? <Tag tone="allow">Loaded</Tag> : <Tag tone="review">Empty</Tag>}
                        {s.last_error && <p className="mt-1 max-w-[220px] text-xs text-block">{s.last_error}</p>}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono tabular-nums text-ink">{s.indicators}</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-ink-muted">{s.last_refresh ? formatTime(s.last_refresh) : 'Never'}</td>
                      <td className="max-w-[220px] px-4 py-2.5 text-xs text-ink-subtle">{s.license}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-4 py-8 text-sm text-ink-subtle">Loading sources.</p>
          )}
        </Panel>

        <Panel>
          <PanelHeader title="Learned from outcomes" subtitle="Only high-confidence outcomes feed back, to avoid snowballing false positives" />
          <dl className="grid grid-cols-2 divide-x divide-line">
            <div className="px-4 py-3">
              <dt className="text-xs text-ink-subtle">Revoked tokens</dt>
              <dd className="font-mono text-2xl text-zombie">{status?.learned.revoked_tokens ?? '–'}</dd>
            </div>
            <div className="px-4 py-3">
              <dt className="text-xs text-ink-subtle">Watched IPs</dt>
              <dd className="font-mono text-2xl text-ink">{status?.learned.watched_ips ?? '–'}</dd>
            </div>
          </dl>
          <p className="border-t border-line px-4 py-3 text-xs text-ink-subtle">
            Tokens are revoked when Zombie Card Saver says so or a card exposure report links to them. IPs are watched for 24 h after a
            trusted compromise.
          </p>
        </Panel>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <Panel>
          <PanelHeader
            title="Card exposure monitoring"
            subtitle="Fingerprints of leaked cards reported by the OnionClaw adapter. Card numbers never reach this system."
          />
          {exposure && !exposure.configured && (
            <div className="p-4">
              <Notice tone="warn" title="Exposure feed not configured">
                Set <code className="font-mono">EXPOSURE_FEED_SECRET</code> and <code className="font-mono">FINGERPRINT_HMAC_SECRET</code> on the
                API, then run <code className="font-mono">scripts/onionclaw_exposure_adapter.py</code> on the collector host.
              </Notice>
            </div>
          )}
          {exposure && (
            <>
              <dl className="grid grid-cols-2 divide-x divide-line border-b border-line">
                <div className="px-4 py-3">
                  <dt className="text-xs text-ink-subtle">Exposed fingerprints</dt>
                  <dd className="font-mono text-2xl text-ink">{exposure.exposed_fingerprints}</dd>
                </div>
                <div className="px-4 py-3">
                  <dt className="text-xs text-ink-subtle">Tokens revoked by exposure</dt>
                  <dd className="font-mono text-2xl text-zombie">{exposure.tokens_revoked_via_exposure}</dd>
                </div>
              </dl>
              {exposure.reports.length === 0 ? (
                <p className="px-4 py-6 text-sm text-ink-subtle">No exposure reports received yet.</p>
              ) : (
                <ul className="divide-y divide-line/60">
                  {exposure.reports.map((r, i) => (
                    <li key={i} className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
                      <span className="text-ink">
                        {r.findings} finding{r.findings === 1 ? '' : 's'} from {r.source}
                        <span className="ml-2 text-xs text-ink-subtle">{r.new} new</span>
                      </span>
                      <span className="text-xs text-ink-muted">
                        {r.tokens_revoked} token{r.tokens_revoked === 1 ? '' : 's'} revoked · <span className="font-mono">{formatTime(r.reported_at)}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </Panel>

        <Panel>
          <PanelHeader title="Recent matches" subtitle="Payments whose source IP, token or card matched an indicator" />
          {matches.length === 0 ? (
            <p className="px-4 py-6 text-sm text-ink-subtle">No matches yet in this session.</p>
          ) : (
            <ul className="max-h-[420px] divide-y divide-line/60 overflow-auto">
              {matches.map((m) => (
                <li key={`${m.event_id}-${m.ts}`} className="px-4 py-2.5 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-ink">{m.matches.map((x) => x.category.replace(/_/g, ' ')).join(', ')}</span>
                    <span className="font-mono text-xs text-ink-subtle">{new Date(m.ts).toLocaleTimeString()}</span>
                  </div>
                  <p className="mt-0.5 font-mono text-xs text-ink-muted">
                    {m.matches.map((x) => `${x.indicator} (${x.source})`).join('  ')}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}
