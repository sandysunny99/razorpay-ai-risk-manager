import { describe, it, expect, vi, beforeAll } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import LiveOperations from '../pages/LiveOperations';
import { LiveEvent } from '../types/api';

const now = Date.now();
const EVENTS: LiveEvent[] = [
  {
    seq: 3, ts: now - 500, tenant_id: 'tenant_123', source: 'generator', scenario: 'forged_signature',
    outcome: 'REJECTED', http_status: 401, rejected_stage: 'hmac', reason: 'Invalid signature', amount: 250, latency_ms: 0.8,
  },
  {
    seq: 2, ts: now - 1000, tenant_id: 'tenant_123', source: 'razorpay', scenario: 'payment.captured', outcome: 'DECIDED',
    decision: 'BLOCK', risk_score: 95, risk_level: 'HIGH', risk_factors: ['critical_amount'], amount: 150000,
    ai_provider: 'UNAVAILABLE', audit_id: 'aud_tenant_123_evt_2', latency_ms: 4.2, event_id: 'evt_2',
  },
  {
    seq: 1, ts: now - 1500, tenant_id: 'tenant_123', source: 'generator', scenario: 'zombie_reuse', outcome: 'DECIDED',
    decision: 'REVIEW', risk_score: 0, risk_level: 'LOW', risk_factors: [], amount: 499,
    zombie: { impact: 'High reuse velocity detected', severity: 'HIGH', recommendation: 'REQUIRE_STEP_UP' },
    ai_provider: 'UNAVAILABLE', audit_id: 'aud_tenant_123_evt_1', latency_ms: 3.1,
  },
];

vi.mock('../hooks/useLiveStream', () => ({
  useLiveStream: () => ({
    events: EVENTS, state: 'live', paused: false, setPaused: vi.fn(), held: false, setHeld: vi.fn(), buffered: 0, clear: vi.fn(),
    generator: { running: true, tenant_id: 'tenant_123', rate_per_sec: 2, attack_ratio: 0.1, risky_ratio: 0.2, emitted: 3, started_at: 0, by_scenario: {} },
    setGenerator: vi.fn(),
  }),
}));
vi.mock('../services/api', () => ({ updateGenerator: vi.fn() }));

beforeAll(() => {
  // Recharts' ResponsiveContainer needs ResizeObserver, which jsdom lacks.
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
});

const renderPage = () => render(<MemoryRouter><LiveOperations /></MemoryRouter>);

describe('LiveOperations', () => {
  it('shows live state, KPIs and every streamed event', () => {
    renderPage();
    expect(screen.getByTestId('stream-state')).toHaveTextContent('Live');
    expect(screen.getAllByTestId('live-row')).toHaveLength(3);
    expect(screen.getByText('Attacks rejected').parentElement?.parentElement).toHaveTextContent('1');
    expect(screen.getAllByText('Forged signature').length).toBeGreaterThan(0);
  });

  it('filters the stream to attacks only', () => {
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: 'Attacks' }));
    const rows = screen.getAllByTestId('live-row');
    expect(rows).toHaveLength(1);
    expect(within(rows[0]).getByText('Rejected')).toBeInTheDocument();
  });

  it('opens an investigation drawer with the pipeline and an audit deep link', () => {
    renderPage();
    fireEvent.click(screen.getAllByTestId('live-row')[1]);
    const dialog = screen.getByRole('dialog', { name: 'Event details' });
    expect(within(dialog).getByTestId('stage-audit')).toHaveAttribute('data-status', 'passed');
    expect(within(dialog).getByTestId('stage-ai')).toHaveAttribute('data-status', 'fallback');
    expect(within(dialog).getByRole('link', { name: /Verify in audit ledger/ })).toHaveAttribute(
      'href',
      '/ledger?id=aud_tenant_123_evt_2',
    );
  });

  it('marks the exact control that rejected an attack', () => {
    renderPage();
    fireEvent.click(screen.getAllByTestId('live-row')[0]);
    const dialog = screen.getByRole('dialog', { name: 'Event details' });
    expect(within(dialog).getByTestId('stage-hmac')).toHaveAttribute('data-status', 'failed');
    expect(within(dialog).getByTestId('stage-risk')).toHaveAttribute('data-status', 'skipped');
  });
});
