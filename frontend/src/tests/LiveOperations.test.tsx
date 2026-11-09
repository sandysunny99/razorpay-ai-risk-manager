import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import LiveOperations from '../pages/LiveOperations';
import * as api from '../services/api';
import { LiveEvent } from '../types/api';

const now = Date.now();
const EVENTS: LiveEvent[] = [
  {
    seq: 4, ts: now - 400, tenant_id: 'tenant_123', source: 'generator', scenario: 'forged_signature',
    outcome: 'REJECTED', http_status: 401, rejected_stage: 'hmac', reason: 'Invalid signature', amount: 250, latency_ms: 0.8,
  },
  {
    seq: 3, ts: now - 800, tenant_id: 'tenant_123', source: 'razorpay', scenario: 'payment.captured', outcome: 'DECIDED',
    decision: 'BLOCK', risk_score: 95, risk_level: 'HIGH', risk_factors: ['critical_amount'], amount: 150000,
    ai_provider: 'UNAVAILABLE', audit_id: 'aud_t_evt_3', latency_ms: 4.2, event_id: 'evt_3', threat: [],
  },
  {
    seq: 2, ts: now - 1200, tenant_id: 'tenant_123', source: 'generator', scenario: 'zombie_reuse', outcome: 'DECIDED',
    decision: 'REVIEW', risk_score: 0, risk_level: 'LOW', risk_factors: [], amount: 499,
    zombie: { impact: 'Expired card credential presented', severity: 'MEDIUM', recommendation: 'REQUIRE_STEP_UP' },
    ai_provider: 'UNAVAILABLE', audit_id: 'aud_t_evt_2', latency_ms: 3.1,
  },
  {
    seq: 1, ts: now - 1600, tenant_id: 'tenant_123', source: 'generator', scenario: 'high_value', outcome: 'DECIDED',
    decision: 'REVIEW', risk_score: 50, risk_level: 'MEDIUM', risk_factors: ['high_amount'], amount: 15000,
    ai_provider: 'UNAVAILABLE', audit_id: 'aud_t_evt_1', latency_ms: 3.0,
  },
];

const markResolved = vi.fn();
vi.mock('../hooks/LiveContext', () => ({
  useLive: () => ({
    events: EVENTS, state: 'live', paused: false, setPaused: vi.fn(), held: false, setHeld: vi.fn(), buffered: 0, clear: vi.fn(),
    generator: { running: true, tenant_id: 'tenant_123', rate_per_sec: 2, attack_ratio: 0.1, risky_ratio: 0.2, emitted: 4, started_at: 0, by_scenario: {} },
    setGenerator: vi.fn(),
    localResolved: new Map([['aud_t_evt_1', 'APPROVE']]),
    markResolved,
  }),
}));
vi.mock('../services/api', () => ({ updateGenerator: vi.fn(), resolveReview: vi.fn() }));

beforeAll(() => {
  // Recharts' ResponsiveContainer needs ResizeObserver, which jsdom lacks.
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
});
beforeEach(() => {
  markResolved.mockReset();
  vi.mocked(api.resolveReview).mockReset();
});

const renderPage = () => render(<MemoryRouter><LiveOperations /></MemoryRouter>);

describe('LiveOperations', () => {
  it('puts unresolved REVIEW decisions in the queue and leaves resolved ones out', () => {
    renderPage();
    const queue = screen.getByRole('list', { name: 'Payments waiting for review' });
    expect(within(queue).getAllByRole('listitem')).toHaveLength(1); // evt_1 already resolved locally
    expect(within(queue).getByText(/Zombie: require step up/i)).toBeInTheDocument();
    expect(screen.getByText('Needs a decision (1)')).toBeInTheDocument();
  });

  it('approving writes a resolution through the API and updates the queue', async () => {
    vi.mocked(api.resolveReview).mockResolvedValueOnce({ audit_id: 'aud_t_evt_2', resolution: 'APPROVE', record_hash: 'h' });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /Approve/ }));
    await waitFor(() => expect(markResolved).toHaveBeenCalledWith('aud_t_evt_2', 'APPROVE'));
    expect(api.resolveReview).toHaveBeenCalledWith('aud_t_evt_2', 'APPROVE');
  });

  it('shows a named error when recording a decision fails', async () => {
    vi.mocked(api.resolveReview).mockRejectedValueOnce(new Error('boom'));
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /Decline/ }));
    expect(await screen.findByText(/Could not record the decision/)).toBeInTheDocument();
    expect(markResolved).not.toHaveBeenCalled();
  });

  it('filters the stream to ingress rejections', () => {
    renderPage();
    expect(screen.getAllByTestId('live-row')).toHaveLength(4);
    fireEvent.click(screen.getByRole('tab', { name: 'Rejected at ingress' }));
    const rows = screen.getAllByTestId('live-row');
    expect(rows).toHaveLength(1);
    expect(within(rows[0]).getByText('HMAC signature')).toBeInTheDocument();
  });

  it('opens the drawer from the keyboard with the stopping control marked', () => {
    renderPage();
    fireEvent.keyDown(screen.getAllByTestId('live-row')[0], { key: 'Enter' });
    const dialog = screen.getByRole('dialog', { name: 'Event details' });
    expect(within(dialog).getByTestId('stage-hmac')).toHaveAttribute('data-status', 'failed');
    expect(within(dialog).getByTestId('stage-risk')).toHaveAttribute('data-status', 'skipped');
  });

  it('links a decided event to its audit record', () => {
    renderPage();
    fireEvent.click(screen.getAllByTestId('live-row')[1]);
    const dialog = screen.getByRole('dialog', { name: 'Event details' });
    expect(within(dialog).getByTestId('stage-ai')).toHaveAttribute('data-status', 'fallback');
    expect(within(dialog).getByRole('link', { name: /audit ledger/ })).toHaveAttribute('href', '/ledger?id=aud_t_evt_3');
  });
});

describe('ML second opinion in the drawer', () => {
  it('shows the score, the escalation and TreeSHAP reasons', () => {
    EVENTS.unshift({
      seq: 9, ts: Date.now() - 100, tenant_id: 'tenant_123', source: 'generator', scenario: 'velocity_burst', outcome: 'DECIDED',
      decision: 'REVIEW', risk_score: 30, risk_level: 'MEDIUM', risk_factors: ['high_velocity'], amount: 900, ai_provider: 'UNAVAILABLE',
      audit_id: 'aud_t_evt_9', latency_ms: 2, pii_masked: ['UPI_ID'],
      ml: { model: 'lightgbm', probability: 0.97, escalated: true, escalation_threshold: 0.8,
        reasons: [{ feature: 'recent payment velocity', direction: 'raises', contribution: 4.7, value: 11 }] },
    });
    render(<MemoryRouter><LiveOperations /></MemoryRouter>);
    fireEvent.click(screen.getAllByTestId('live-row')[0]);
    const dialog = screen.getByRole('dialog', { name: 'Event details' });
    expect(within(dialog).getByText('score 0.97')).toBeInTheDocument();
    expect(within(dialog).getByText(/sent an otherwise allowed payment to review/)).toBeInTheDocument();
    expect(within(dialog).getByText(/recent payment velocity/)).toBeInTheDocument();
    expect(within(dialog).getByText(/masked in the payment note/)).toBeInTheDocument();
    expect(within(dialog).getByTestId('stage-ml')).toHaveAttribute('data-status', 'passed');
    EVENTS.shift();
  });
});
