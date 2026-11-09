import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Activity, Menu, PanelLeftClose, PanelLeftOpen, Plug, ScrollText, Search, ShieldAlert, X } from 'lucide-react';
import { LiveProvider, useLive } from '../hooks/LiveContext';
import { DEMO_TENANT } from '../services/api';
import CommandPalette from '../components/CommandPalette';
import { cx } from '../components/ui';
import { pendingReviews, resolutionsFrom, trafficEvents } from '../utils/liveMetrics';

const NAV = [
  { to: '/', label: 'Live operations', icon: Activity, end: true },
  { to: '/threats', label: 'Threat intelligence', icon: ShieldAlert, end: false },
  { to: '/ledger', label: 'Audit ledger', icon: ScrollText, end: false },
  { to: '/integrations', label: 'Integrations', icon: Plug, end: false },
];

/** Shield mark: a flat monoline outline. No gradient, glow or AI sparkle (anti-slop R-01, R-04). */
function Mark() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden className="shrink-0">
      <path d="M12 2.5 4 5.5v6.2c0 4.6 3.3 8.3 8 9.8 4.7-1.5 8-5.2 8-9.8V5.5z" fill="none" stroke="#ecebe7" strokeWidth="1.6" />
      <path d="M8.5 12.2 11 14.6l4.6-5" fill="none" stroke="#ecebe7" strokeWidth="1.6" />
    </svg>
  );
}

function Sidebar({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const { events, localResolved } = useLive();
  const traffic = trafficEvents(events);
  const resolved = resolutionsFrom(events);
  localResolved.forEach((v, k) => resolved.set(k, v));
  const waiting = pendingReviews(traffic, resolved).length;

  return (
    <div className="flex h-full flex-col">
      <div className={cx('flex items-center gap-2.5 py-4', collapsed ? 'justify-center px-2' : 'px-4')}>
        <Mark />
        {!collapsed && (
          <div>
            <p className="text-[15px] font-semibold leading-tight text-ink">Netvrio</p>
            <p className="text-xs leading-tight text-ink-subtle">Payment risk console</p>
          </div>
        )}
      </div>
      <nav className="flex-1 space-y-0.5 px-2" aria-label="Main">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              cx(
                'flex min-h-[40px] items-center gap-3 rounded border-l-2 px-3 text-sm',
                collapsed && 'justify-center px-0',
                isActive ? 'border-ink bg-raised text-ink' : 'border-transparent text-ink-muted hover:bg-raised hover:text-ink',
              )
            }
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden />
            {!collapsed && <span className="flex-1">{label}</span>}
            {!collapsed && to === '/' && waiting > 0 && (
              <span className="font-mono text-xs text-review" aria-label={`${waiting} waiting for review`}>{waiting}</span>
            )}
          </NavLink>
        ))}
      </nav>
      {!collapsed && (
        <div className="m-3 border-t border-line pt-3 text-xs text-ink-subtle">
          <p>
            Tenant <code className="font-mono text-ink-muted">{DEMO_TENANT}</code>
          </p>
          <p className="mt-1">Demo tenant header. Production sign-in is not connected yet.</p>
        </div>
      )}
    </div>
  );
}

const TITLES: Record<string, string> = {
  '/': 'Live operations',
  '/threats': 'Threat intelligence',
  '/ledger': 'Audit ledger',
  '/integrations': 'Integrations',
};

function Shell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen((o) => !o);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <aside
        className={cx(
          'fixed inset-y-0 left-0 z-30 hidden border-r border-line bg-surface lg:block',
          collapsed ? 'w-16' : 'w-60',
        )}
      >
        <Sidebar collapsed={collapsed} />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-line bg-surface">
            <button
              className="absolute right-2 top-3 flex h-11 w-11 items-center justify-center text-ink-muted hover:text-ink"
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation"
            >
              <X className="h-5 w-5" />
            </button>
            <Sidebar collapsed={false} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className={collapsed ? 'lg:pl-16' : 'lg:pl-60'}>
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-line bg-canvas px-3 sm:px-5">
          <button
            className="flex h-11 w-11 items-center justify-center text-ink-muted hover:text-ink lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </button>
          <button
            className="hidden h-9 w-9 cursor-pointer items-center justify-center rounded text-ink-muted hover:bg-raised hover:text-ink lg:flex"
            onClick={() => setCollapsed((c) => !c)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </button>
          <nav aria-label="Breadcrumb" className="min-w-0 flex-1 truncate text-sm">
            <span className="text-ink-subtle">Netvrio</span>
            <span className="mx-2 text-ink-subtle">/</span>
            <span className="text-ink">{TITLES[pathname] ?? 'Page'}</span>
          </nav>
          <button
            onClick={() => setPaletteOpen(true)}
            className="flex h-9 cursor-pointer items-center gap-2 rounded border border-line px-2.5 text-sm text-ink-subtle hover:border-line-strong hover:text-ink"
            aria-label="Open command palette (Ctrl+K)"
          >
            <Search className="h-4 w-4" aria-hidden />
            <span className="hidden sm:inline">Commands</span>
            <kbd className="hidden font-mono text-xs sm:inline">Ctrl K</kbd>
          </button>
        </header>
        <div className="border-b border-line bg-surface px-3 py-1.5 text-xs text-ink-muted sm:px-5">
          Prototype on test data: synthetic traffic plus Razorpay test-mode and YouPI webhooks. No real cardholder data. AI output is advisory only.
        </div>

        <main className="mx-auto w-full max-w-[1400px] px-3 py-5 sm:px-5">
          <Outlet />
        </main>
      </div>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}

export default function MainLayout() {
  return (
    <LiveProvider>
      <Shell />
    </LiveProvider>
  );
}
