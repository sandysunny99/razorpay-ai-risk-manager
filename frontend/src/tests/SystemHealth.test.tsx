import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SystemHealth from '../pages/SystemHealth';
import * as api from '../services/api';

vi.mock('../services/api', () => ({
  API_BASE_URL: '',
  getProviderHealth: vi.fn(),
  getRazorpayStatus: vi.fn(() => new Promise(() => undefined)),
}));

describe('SystemHealth', () => {
  beforeEach(() => {
    vi.mocked(api.getProviderHealth).mockReset();
  });

  it('renders API-returned provider statuses', async () => {
    vi.mocked(api.getProviderHealth).mockResolvedValue({
      primary: "NOT VERIFIED / CONTRACT TESTED",
      secondary: "UNAVAILABLE",
      fallback: "MISCONFIGURED"
    } as any);

    render(<SystemHealth />);

    await waitFor(() => {
      expect(screen.getByText('Cloudflare / Primary')).toBeInTheDocument();
      expect(screen.getByText('NOT VERIFIED / CONTRACT TESTED')).toBeInTheDocument();
      expect(screen.getByText('UNAVAILABLE')).toBeInTheDocument();
      expect(screen.getByText('MISCONFIGURED')).toBeInTheDocument();
    });
  });

  it('handles API rejection safely', async () => {
    vi.mocked(api.getProviderHealth).mockRejectedValue(new Error('Network error'));

    render(<SystemHealth />);

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toHaveTextContent('An unexpected application error occurred.');
    });
  });
});
