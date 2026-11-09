import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Menu, Plug, Radar, ScrollText, ShieldCheck, X } from 'lucide-react';
import { DEMO_TENANT, getHealth } from '../services/api';
import { cx } from '../components/ui';

const NAV = [
  { to: '/', label: 'Live Operations', icon: Radar, end: true },
  { to: '/ledger', label: 'Audit Ledger', icon: ScrollText, end: false },
  { to: '/integrations', label: 'Integrations', icon: Plug, end: false },
];

type ApiState = 'checking' | 'online' | 'offline';

function useApiState(): ApiState {
  const [state, setState] = useState<ApiState>('checking');
  useEffect(() => {
    let alive = true;
    const check = () =>
      getHealth()
        .then(() => alive && setState('online'))
        .catch(() => alive && setState('offline'));
    check();
    const id = window.setInterval(check, 15000);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, []);
  return state;
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const api = useApiState();
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-400 shadow-lg shadow-indigo-500/20">
          <ShieldCheck className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-base font-semibold leading-tight text-white">Netvrio</p>
          <p className="text-[11px] leading-tight text-slate-400">Payment Risk &amp; Security</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3" aria-label="Main">
        {NAV.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cx(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive ? 'bg-indigo-500/15 text-white ring-1 ring-inset ring-indigo-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100',
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="m-3 space-y-2 rounded-lg border border-slate-800 bg-slate-900/80 p-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">API</span>
          <span className="flex items-center gap-1.5 font-medium">
            <span
              className={cx(
                'h-2 w-2 rounded-full',
                api === 'online' && 'bg-emerald-400 shadow-[0_0_8px] shadow-emerald-400/60',
                api === 'offline' && 'bg-rose-500',
                api === 'checking' && 'bg-slate-500',
              )}
            />
            <span className={api === 'online' ? 'text-emerald-300' : api === 'offline' ? 'text-rose-300' : 'text-slate-400'}>
              {api === 'online' ? 'Online' : api === 'offline' ? 'Offline' : 'Checking'}
            </span>
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Tenant</span>
          <code className="rounded bg-slate-800 px-1.5 py-0.5 text-[11px] text-slate-200">{DEMO_TENANT}</code>
        </div>
        <p className="pt-1 text-[11px] leading-snug text-slate-500">Demo tenant context. Production authentication is not connected.</p>
      </div>
    </div>
  );
}

export default function MainLayout() {
  const [open, setOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-slate-800 bg-slate-950 lg:block">
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-slate-800 bg-slate-950">
            <button
              className="absolute right-3 top-5 rounded p-1 text-slate-400 hover:text-white"
              onClick={() => setOpen(false)}
              aria-label="Close navigation"
            >
              <X className="h-5 w-5" />
            </button>
            <Sidebar onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <div className="sticky top-0 z-20 border-b border-amber-500/20 bg-amber-500/10 backdrop-blur">
          <div className="flex items-center gap-3 px-4 py-2 sm:px-6">
            <button
              className="rounded p-1 text-slate-300 hover:text-white lg:hidden"
              onClick={() => setOpen(true)}
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-300">
              Prototype · test-mode data only
            </p>
            <p className="hidden text-xs text-amber-200/70 md:block">
              Synthetic traffic and Razorpay test-mode webhooks. No real cardholder data. AI output is advisory only.
            </p>
          </div>
        </div>

        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
