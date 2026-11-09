import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PipelineTimeline, { failedAt, PIPELINE } from '../components/PipelineTimeline';
import '@testing-library/jest-dom';

describe('PipelineTimeline', () => {
  it('marks earlier stages verified, the failing stage blocked and later stages not reached', () => {
    render(<PipelineTimeline status={failedAt('tenant')} />);
    expect(screen.getByTestId('stage-hmac')).toHaveAttribute('data-status', 'passed');
    expect(screen.getByTestId('stage-schema')).toHaveAttribute('data-status', 'passed');
    expect(screen.getByTestId('stage-tenant')).toHaveAttribute('data-status', 'failed');
    expect(screen.getByTestId('stage-risk')).toHaveAttribute('data-status', 'skipped');
    expect(screen.getByTestId('stage-audit')).toHaveAttribute('data-status', 'skipped');
  });

  it('orders ingress controls before analysis, matching the backend route', () => {
    const ids = PIPELINE.map((s) => s.id);
    expect(ids.indexOf('hmac')).toBeLessThan(ids.indexOf('replay'));
    expect(ids.indexOf('pan')).toBeLessThan(ids.indexOf('idempotency'));
    expect(ids.indexOf('ai')).toBeLessThan(ids.indexOf('policy'));
  });
});
