import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import SystemHealth from '../pages/SystemHealth';
import * as api from '../services/api';

vi.mock('../services/api', () => ({
  API_BASE_URL: '',
  getProviderHealth: vi.fn(),
  verifyProviders: vi.fn(),
  getHealth: vi.fn(() => Promise.resolve({ status: 'ok' })),
  getRazorpayStatus: vi.fn(() => new Promise(() => undefined)),
  getYoupiStatus: vi.fn(() => new Promise(() => undefined)),
  getComponents: vi.fn(() => new Promise(() => undefined)),
  updateGenerator: vi.fn(),
}));
vi.mock('../hooks/LiveContext', () => ({
  useLive: () => ({ generator: null, setGenerator: vi.fn(), state: 'live' }),
}));

const chainRow = (name: string, status: string, configured = true) => ({
  name, configured, model: configured ? `${name}-model` : null, status, latency_ms: null, detail: null, checked_at: null,
});

describe('SystemHealth', () => {
  beforeEach(() => {
    vi.mocked(api.getProviderHealth).mockReset();
    vi.mocked(api.verifyProviders).mockReset();
  });

  it('renders the real provider chain in order', async () => {
    vi.mocked(api.getProviderHealth).mockResolvedValue({
      primary: 'NOT VERIFIED / CONTRACT TESTED', secondary: 'MISCONFIGURED', fallback: 'MISCONFIGURED',
      chain: [chainRow('groq', 'NOT VERIFIED'), chainRow('cloudflare', 'NOT VERIFIED'), chainRow('nvidia', 'NOT CONFIGURED', false)],
      scope: 'flagged', budget: { used_last_minute: 3, limit_per_minute: 20 },
    } as never);
    render(<SystemHealth />);
    await waitFor(() => expect(screen.getByText('Groq')).toBeInTheDocument());
    expect(screen.getByText('Cloudflare Workers AI')).toBeInTheDocument();
    expect(screen.getByText('No key set')).toBeInTheDocument();
    expect(screen.getByText(/3 of 20 calls/)).toBeInTheDocument();
  });

  it('verify updates statuses with latency', async () => {
    vi.mocked(api.getProviderHealth).mockResolvedValue({ primary: 'x', secondary: 'x', fallback: 'x', chain: [chainRow('groq', 'NOT VERIFIED')] } as never);
    vi.mocked(api.verifyProviders).mockResolvedValue({
      primary: 'x', secondary: 'x', fallback: 'x', chain: [{ ...chainRow('groq', 'AVAILABLE'), latency_ms: 1384 }],
    } as never);
    render(<SystemHealth />);
    fireEvent.click(await screen.findByRole('button', { name: /Verify now/ }));
    expect(await screen.findByText('Answering')).toBeInTheDocument();
    expect(screen.getByText('1384 ms')).toBeInTheDocument();
  });

  it('handles API rejection safely', async () => {
    vi.mocked(api.getProviderHealth).mockRejectedValue(new Error('Network error'));
    render(<SystemHealth />);
    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent('An unexpected application error occurred.');
    });
  });
});
