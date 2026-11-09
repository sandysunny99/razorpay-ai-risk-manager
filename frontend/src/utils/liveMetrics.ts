import { LiveEvent } from '../types/api';

export const EMPTY = '–';

export const STAGE_LABELS: Record<string, string> = {
  hmac: 'HMAC signature',
  schema: 'Strict schema',
  tenant: 'Tenant binding',
  pan: 'Raw PAN guard',
  replay: 'Replay window',
  idempotency: 'Idempotency',
  unknown: 'Other',
};

export const SCENARIO_LABELS: Record<string, string> = {
  normal: 'Payment',
  high_value: 'High-value payment',
  very_high_value: 'Very high value',
  velocity_burst: 'Velocity burst',
  zombie_reuse: 'Dead token reuse',
  compromised_token: 'Compromised token',
  threat_ip: 'Listed source IP',
  'upi.observed_success': 'UPI observed (unreconciled)',
  'upi.reconciled': 'UPI reconciled',
  'payment.captured': 'Razorpay captured',
  'payment.authorized': 'Razorpay authorized',
  'payment.failed': 'Razorpay failed',
  forged_signature: 'Forged signature',
  replay_stale: 'Stale replay',
  duplicate_delivery: 'Duplicate delivery',
  cross_tenant: 'Cross-tenant injection',
  raw_pan: 'Raw PAN submitted',
};

export function eventLabel(e: LiveEvent): string {
  return SCENARIO_LABELS[e.scenario ?? ''] ?? e.event_type ?? 'Payment';
}

export type Verdict = 'ALLOW' | 'REVIEW' | 'BLOCK' | 'REJECTED';

export function verdictOf(e: LiveEvent): Verdict {
  if (e.outcome === 'REJECTED') return 'REJECTED';
  if (e.decision === 'BLOCK' || e.decision === 'QUARANTINE') return 'BLOCK';
  if (e.decision === 'REVIEW') return 'REVIEW';
  return 'ALLOW';
}

/** Pipeline outcomes only; resolutions and exposure reports are bookkeeping, not traffic. */
export function trafficEvents(events: LiveEvent[]): LiveEvent[] {
  return events.filter((e) => e.outcome === 'DECIDED' || e.outcome === 'REJECTED');
}

/** audit_id -> resolution, from RESOLVED events seen on the stream. */
export function resolutionsFrom(events: LiveEvent[]): Map<string, 'APPROVE' | 'DECLINE'> {
  const map = new Map<string, 'APPROVE' | 'DECLINE'>();
  for (const e of events) if (e.outcome === 'RESOLVED' && e.resolves && e.resolution) map.set(e.resolves, e.resolution);
  return map;
}

/** REVIEW decisions still waiting for a human, newest first. */
export function pendingReviews(events: LiveEvent[], resolved: Map<string, unknown>): LiveEvent[] {
  return events.filter((e) => e.outcome === 'DECIDED' && e.decision === 'REVIEW' && e.audit_id && !resolved.has(e.audit_id));
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
  threatHits: number;
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
export function computeMetrics(allEvents: LiveEvent[], now: number = Date.now(), windowSec = 180, bucketSec = 5): LiveMetrics {
  const events = trafficEvents(allEvents);
  let allow = 0, review = 0, block = 0, rejected = 0, zombies = 0, threatHits = 0, volumeAllowed = 0, volumeStopped = 0;
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
    if (e.threat && e.threat.length) threatHits++;
    if (typeof e.latency_ms === 'number') latencies.push(e.latency_ms);
    if (typeof e.amount === 'number' && v !== 'REJECTED') {
      if (v === 'ALLOW') volumeAllowed += e.amount;
      else if (v === 'BLOCK') volumeStopped += e.amount;
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
    threatHits,
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
  if (typeof amount !== 'number') return EMPTY;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: compact ? 1 : 2,
    notation: compact ? 'compact' : 'standard',
  }).format(amount);
}
