import { describe, it, expect, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import '@testing-library/jest-dom';
import CommandPalette from '../components/CommandPalette';
import * as api from '../services/api';

const setPaused = vi.fn();
vi.mock('../hooks/LiveContext', () => ({
  useLive: () => ({ paused: false, setPaused, generator: null, setGenerator: vi.fn() }),
}));
vi.mock('../services/api', () => ({ updateGenerator: vi.fn(), refreshIntelFeeds: vi.fn(), verifyLedgerFull: vi.fn() }));

function Where() {
  return <p data-testid="where">{useLocation().pathname + useLocation().search}</p>;
}

const renderPalette = (onClose = vi.fn()) =>
  render(
    <MemoryRouter>
      <CommandPalette open onClose={onClose} />
      <Routes>
        <Route path="*" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );

describe('CommandPalette', () => {
  it('filters commands and navigates with the keyboard', () => {
    const onClose = vi.fn();
    renderPalette(onClose);
    fireEvent.change(screen.getByLabelText('Command'), { target: { value: 'threat intel' } });
    fireEvent.keyDown(screen.getByLabelText('Command'), { key: 'Enter' });
    expect(screen.getByTestId('where')).toHaveTextContent('/threats');
    expect(onClose).toHaveBeenCalled();
  });

  it('opens an audit record from a pasted ID', () => {
    renderPalette();
    fireEvent.change(screen.getByLabelText('Command'), { target: { value: 'aud_tenant_123_evt_9' } });
    fireEvent.keyDown(screen.getByLabelText('Command'), { key: 'Enter' });
    expect(screen.getByTestId('where')).toHaveTextContent('/ledger?id=aud_tenant_123_evt_9');
  });

  it('runs the full ledger verification and reports the result', async () => {
    vi.mocked(api.verifyLedgerFull).mockResolvedValueOnce({ chain_verified: true, scope: 'full' });
    renderPalette();
    fireEvent.click(screen.getByRole('button', { name: /Verify the whole audit ledger/ }));
    expect(await screen.findByRole('status')).toHaveTextContent('hash chain intact');
  });
});
