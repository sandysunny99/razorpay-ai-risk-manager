// frontend/src/hooks/useRiskEventStream.ts
/**
 * Phase 4 — Real-Time Risk Event Stream Hook
 * -------------------------------------------
 * Connects to the SSE endpoint at /api/v1/stream/risk-events.
 * Automatically reconnects with exponential backoff on network drops.
 * Backoff: starts at 1s, doubles on each failure, caps at 30s.
 * Resets to 1s after a successful connection.
 */
import { useCallback, useEffect, useRef, useState } from 'react';

export interface RiskStreamEvent {
  event_type: string;
  risk_score?: number;
  severity?: string;
  transaction_id?: string;
  card_masked?: string;
  merchant_id?: string;
  policy_decision?: string;
  timestamp?: string;
  [key: string]: unknown;
}

export interface UseRiskEventStreamResult {
  events: RiskStreamEvent[];
  isConnected: boolean;
  error: string | null;
  clearEvents: () => void;
}

const MAX_EVENTS = 200; // Rolling window — keep only the latest N events

export function useRiskEventStream(
  url: string = '/api/v1/stream/risk-events',
): UseRiskEventStreamResult {
  const [events, setEvents] = useState<RiskStreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refs so the reconnect loop doesn't close over stale state
  const esRef = useRef<EventSource | null>(null);
  const backoffRef = useRef<number>(1000); // ms
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  const clearEvents = useCallback(() => setEvents([]), []);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    // Close any existing connection
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }

    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => {
      if (unmountedRef.current) return;
      setIsConnected(true);
      setError(null);
      backoffRef.current = 1000; // Reset backoff on success
    };

    es.onmessage = (evt) => {
      if (unmountedRef.current) return;
      try {
        const parsed: RiskStreamEvent = JSON.parse(evt.data);
        setEvents((prev) => {
          const updated = [parsed, ...prev];
          return updated.slice(0, MAX_EVENTS);
        });
      } catch {
        // Ignore malformed events
      }
    };

    es.onerror = () => {
      if (unmountedRef.current) return;
      setIsConnected(false);
      es.close();
      esRef.current = null;

      const delay = backoffRef.current;
      // Exponential backoff: double each time, cap at 30s
      backoffRef.current = Math.min(backoffRef.current * 2, 30_000);
      setError(`Stream disconnected. Reconnecting in ${Math.round(delay / 1000)}s…`);

      retryTimerRef.current = setTimeout(() => {
        if (!unmountedRef.current) connect();
      }, delay);
    };
  }, [url]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
    };
  }, [connect]);

  return { events, isConnected, error, clearEvents };
}
