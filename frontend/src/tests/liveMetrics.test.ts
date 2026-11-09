import { describe, it, expect } from 'vitest';
import { computeMetrics, percentile, verdictOf } from '../utils/liveMetrics';
import { LiveEvent } from '../types/api';

const NOW = 1_800_000_000_000;
let seq = 0;
const ev = (partial: Partial<LiveEvent>): LiveEvent => ({
  seq: ++seq,
  ts: NOW - 1000,
  tenant_id: 't',
  source: 'generator',
  outcome: 'DECIDED',
  ...partial,
});

describe('liveMetrics', () => {
  it('classifies verdicts, counting QUARANTINE as a block and rejections separately', () => {
    expect(verdictOf(ev({ decision: 'ALLOW' }))).toBe('ALLOW');
    expect(verdictOf(ev({ decision: 'QUARANTINE' }))).toBe('BLOCK');
    expect(verdictOf(ev({ outcome: 'REJECTED', rejected_stage: 'hmac' }))).toBe('REJECTED');
  });

  it('computes rates, attack breakdown, histogram and rolling throughput', () => {
    const events = [
      ev({ decision: 'ALLOW', risk_score: 0, amount: 100, latency_ms: 2 }),
      ev({ decision: 'ALLOW', risk_score: 5, amount: 200, latency_ms: 4 }),
      ev({ decision: 'REVIEW', risk_score: 50, amount: 15000, latency_ms: 6 }),
      ev({ decision: 'BLOCK', risk_score: 95, amount: 120000, latency_ms: 8, zombie: { impact: 'x', severity: 'HIGH', recommendation: 'REVOKE_TOKEN' } }),
      ev({ outcome: 'REJECTED', rejected_stage: 'hmac', latency_ms: 1 }),
      ev({ outcome: 'REJECTED', rejected_stage: 'hmac', latency_ms: 1 }),
      ev({ outcome: 'REJECTED', rejected_stage: 'tenant', latency_ms: 1, ts: NOW - 60_000 }),
    ];
    const m = computeMetrics(events, NOW);
    expect(m.decided).toBe(4);
    expect(m.approvalRate).toBe(50);
    expect(m.rejected).toBe(3);
    expect(m.zombies).toBe(1);
    expect(m.volumeAllowed).toBe(300);
    expect(m.volumeStopped).toBe(120000); // BLOCK only; review is not yet stopped
    expect(m.byStage[0]).toMatchObject({ stage: 'hmac', count: 2 });
    expect(m.riskHistogram[0].count).toBe(2);
    expect(m.riskHistogram[9].count).toBe(1);
    expect(m.tps).toBe(0.6); // 6 events within the last 10 s
    const totalInTimeline = m.timeline.reduce((a, b) => a + b.ALLOW + b.REVIEW + b.BLOCK + b.REJECTED, 0);
    expect(totalInTimeline).toBe(7);
  });

  it('percentile handles empty and small samples', () => {
    expect(percentile([], 95)).toBeNull();
    expect(percentile([3, 1, 2], 50)).toBe(2);
    expect(percentile([3, 1, 2], 95)).toBe(3);
  });
});
