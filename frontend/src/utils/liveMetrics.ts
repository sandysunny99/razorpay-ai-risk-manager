import { LiveEvent } from '../types/api';

export const STAGE_LABELS: Record<string, string> = {
  hmac: 'HMAC signature',
  schema: 'Strict schema',
  tenant: 'Tenant binding',
  pan: 'Raw PAN guard',
  replay: 'Replay / duplicate',
  idempotency: 'Idempotency',
  unknown: 'Other',
};

export const SCENARIO_LABELS: Record<string, string> = {
  normal: 'Normal payment',
  high_value: 'High-value payment',
  very_high_value: 'Very high value',
  velocity_burst: 'Velocity burst',
  zombie_reuse: 'Dead token reuse',
  compromised_token: 'Compromised token',
  forged_signature: 'Forged signature',
  replay_stale: 'Stale replay',
  duplicate_delivery: 'Duplicate delivery',
  cross_tenant: 'Cross-tenant injection',
  raw_pan: 'Raw PAN submitted',
};

export type Verdict = 'ALLOW' | 'REVIEW' | 'BLOCK' | 'REJECTED';

export function verdictOf(e: LiveEvent): Verdict {
  if (e.outcome === 'REJECTED') return 'REJECTED';
  if (e.decision === 'BLOCK' || e.decision === 'QUARANTINE') return 'BLOCK';
  if (e.decision === 'REVIEW') return 'REVIEW';
  return 'ALLOW';
}

export function percentile(values: number[], p: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[idx];
}

export interface LiveMetrics {
  total: number;
  decided: number;
  rejected: number;
  allow: number;
  review: number;
  block: number;
  zombies: number;
  tps: number;
  approvalRate: number | null;
  p50: number | null;
  p95: number | null;
  volumeAllowed: number;
  volumeStopped: number;
  byStage: { stage: string; label: string; count: number }[];
  timeline: { t: string; ALLOW: number; REVIEW: number; BLOCK: number; REJECTED: number }[];
  riskHistogram: { bucket: string; count: number }[];
}

/** Derive dashboard metrics from the live event buffer. `now` is injectable for tests. */
export function computeMetrics(events: LiveEvent[], now: number = Date.now(), windowSec = 180, bucketSec = 5): LiveMetrics {
  let allow = 0, review = 0, block = 0, rejected = 0, zombies = 0, volumeAllowed = 0, volumeStopped = 0;
  const latencies: number[] = [];
  const stageCounts: Record<string, number> = {};
  const hist = new Array(10).fill(0);
  const bucketCount = Math.floor(windowSec / bucketSec);
  const start = now - windowSec * 1000;
  const buckets = Array.from({ length: bucketCount }, (_, i) => ({
    t: `-${windowSec - i * bucketSec}s`,
    ALLOW: 0, REVIEW: 0, BLOCK: 0, REJECTED: 0,
  }));
  let recent = 0;

  for (const e of events) {
    const v = verdictOf(e);
    if (v === 'ALLOW') allow++;
    else if (v === 'REVIEW') review++;
    else if (v === 'BLOCK') block++;
    else rejected++;
    if (e.zombie) zombies++;
    if (typeof e.latency_ms === 'number') latencies.push(e.latency_ms);
    if (typeof e.amount === 'number') {
      if (v === 'ALLOW') volumeAllowed += e.amount;
      else volumeStopped += e.amount;
    }
    if (v === 'REJECTED') {
      const s = e.rejected_stage ?? 'unknown';
      stageCounts[s] = (stageCounts[s] ?? 0) + 1;
    } else if (typeof e.risk_score === 'number') {
      hist[Math.min(9, Math.floor(e.risk_score / 10))]++;
    }
    if (e.ts >= start && e.ts <= now) {
      const idx = Math.min(bucketCount - 1, Math.floor((e.ts - start) / (bucketSec * 1000)));
      buckets[idx][v]++;
    }
    if (e.ts >= now - 10_000) recent++;
  }

  const decided = allow + review + block;
  return {
    total: events.length,
    decided,
    rejected,
    allow,
    review,
    block,
    zombies,
    tps: Math.round((recent / 10) * 10) / 10,
    approvalRate: decided ? Math.round((allow / decided) * 1000) / 10 : null,
    p50: percentile(latencies, 50),
    p95: percentile(latencies, 95),
    volumeAllowed,
    volumeStopped,
    byStage: Object.entries(stageCounts)
      .map(([stage, count]) => ({ stage, label: STAGE_LABELS[stage] ?? stage, count }))
      .sort((a, b) => b.count - a.count),
    timeline: buckets,
    riskHistogram: hist.map((count, i) => ({ bucket: `${i * 10}`, count })),
  };
}

export function formatInr(amount: number | null | undefined, compact = false): string {
  if (typeof amount !== 'number') return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: compact ? 1 : 2,
    notation: compact ? 'compact' : 'standard',
  }).format(amount);
}
