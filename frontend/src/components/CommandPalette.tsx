import { KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useLive } from '../hooks/LiveContext';
import { refreshIntelFeeds, updateGenerator, verifyLedgerFull } from '../services/api';
import { getErrorStatus, getSafeApiError } from '../utils/errors';
import { cx } from './ui';

interface Command {
  id: string;
  label: string;
  hint: string;
  run: () => Promise<string | void> | string | void;
}

/** Ctrl/⌘K palette. Every command performs a real action; results are reported inline. */
export default function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const live = useLive();
  const [query, setQuery] = useState('');
  const [active, setActive] = useState(0);
  const [result, setResult] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQuery('');
      setActive(0);
      setResult(null);
    }
  }, [open]);

  const commands = useMemo<Command[]>(() => {
    const go = (path: string, label: string): Command => ({ id: `go-${path}`, label, hint: 'Go to', run: () => { navigate(path); onClose(); } });
    const list: Command[] = [
      go('/', 'Live operations'),
      go('/threats', 'Threat intelligence'),
      go('/ledger', 'Audit ledger'),
      go('/integrations', 'Integrations'),
      {
        id: 'stream',
        label: live.paused ? 'Resume event stream' : 'Pause event stream',
        hint: 'Stream',
        run: () => { live.setPaused(!live.paused); onClose(); },
      },
      {
        id: 'verify',
        label: 'Verify the whole audit ledger now',
        hint: 'Ledger',
        run: async () => ((await verifyLedgerFull()).chain_verified ? 'Full ledger verified: hash chain intact.' : 'Hash chain broken. Investigate the ledger.'),
      },
      {
        id: 'feeds',
        label: 'Refresh threat feeds',
        hint: 'Threat intel',
        run: async () => {
          try {
            const r = await refreshIntelFeeds();
            const parts = Object.entries(r.results).map(([k, v]) => `${k}: ${v < 0 ? 'failed' : `${v} indicators`}`);
            return parts.length ? parts.join(', ') : 'Live feeds are off (NETVRIO_TI_LIVE_FEEDS=false).';
          } catch (err) {
            return getErrorStatus(err) === 404 ? 'Feed refresh needs demo mode on the API.' : getSafeApiError(err);
          }
        },
      },
    ];
    if (live.generator) {
      const running = live.generator.running;
      list.push({
        id: 'traffic',
        label: running ? 'Stop synthetic traffic' : 'Start synthetic traffic',
        hint: 'Traffic',
        run: async () => {
          live.setGenerator(await updateGenerator({ running: !running }));
          return running ? 'Synthetic traffic stopped.' : 'Synthetic traffic started.';
        },
      });
    }
    const q = query.trim();
    if (/^aud_[\w-]+$/.test(q)) {
      list.unshift({ id: 'open-audit', label: `Open audit record ${q}`, hint: 'Ledger', run: () => { navigate(`/ledger?id=${encodeURIComponent(q)}`); onClose(); } });
    }
    return list;
  }, [live, navigate, onClose, query]);

  const visible = commands.filter((c) => c.id === 'open-audit' || `${c.hint} ${c.label}`.toLowerCase().includes(query.trim().toLowerCase()));

  const execute = async (c: Command) => {
    setRunning(true);
    try {
      const msg = await c.run();
      if (msg) setResult(msg);
    } catch (err) {
      setResult(getSafeApiError(err));
    } finally {
      setRunning(false);
    }
  };

  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
    else if (e.key === 'ArrowDown') { e.preventDefault(); setActive((a) => Math.min(visible.length - 1, a + 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => Math.max(0, a - 1)); }
    else if (e.key === 'Enter' && visible[active]) { e.preventDefault(); execute(visible[active]); }
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-[12vh]" role="dialog" aria-modal="true" aria-label="Command palette">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-lg overflow-hidden rounded-md border border-line-strong bg-surface shadow-2xl" onKeyDown={onKey}>
        <div className="flex items-center gap-2 border-b border-line px-3">
          <Search className="h-4 w-4 text-ink-subtle" aria-hidden />
          <input
            ref={inputRef}
            autoFocus
            value={query}
            onChange={(e) => { setQuery(e.target.value); setActive(0); setResult(null); }}
            placeholder="Type a command or paste an audit ID"
            aria-label="Command"
            className="w-full bg-transparent py-3 text-sm text-ink placeholder:text-ink-subtle focus:outline-none"
          />
        </div>
        <ul className="max-h-72 overflow-auto py-1" role="listbox" aria-label="Commands">
          {visible.length === 0 && <li className="px-4 py-3 text-sm text-ink-subtle">No command matches "{query}".</li>}
          {visible.map((c, i) => (
            <li key={c.id} role="option" aria-selected={i === active}>
              <button
                onMouseEnter={() => setActive(i)}
                onClick={() => execute(c)}
                disabled={running}
                className={cx('flex w-full cursor-pointer items-center justify-between px-4 py-2 text-left text-sm', i === active ? 'bg-raised text-ink' : 'text-ink-muted')}
              >
                <span>{c.label}</span>
                <span className="text-xs text-ink-subtle">{c.hint}</span>
              </button>
            </li>
          ))}
        </ul>
        {result && <p className="border-t border-line px-4 py-2.5 text-sm text-ink" role="status">{result}</p>}
      </div>
    </div>
  );
}
