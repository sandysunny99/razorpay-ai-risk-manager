import { useCallback, useEffect, useRef, useState } from 'react';
import { getLiveSnapshot, liveStreamUrl } from '../services/api';
import { GeneratorStatus, LiveEvent } from '../types/api';

export type StreamState = 'connecting' | 'live' | 'reconnecting' | 'offline';

const MAX_EVENTS = 600;

function mergeNewestFirst(existing: LiveEvent[], incoming: LiveEvent[]): LiveEvent[] {
  const seen = new Set(existing.map((e) => e.seq));
  const fresh = incoming.filter((e) => !seen.has(e.seq));
  if (fresh.length === 0) return existing;
  return [...fresh.sort((a, b) => b.seq - a.seq), ...existing].slice(0, MAX_EVENTS);
}

/**
 * Subscribes to the backend's Server-Sent Events feed of pipeline decisions.
 * Seeds from /live/snapshot, then appends live events; EventSource reconnects automatically.
 * While paused, events are buffered (not dropped) and released on resume.
 */
export function useLiveStream() {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [state, setState] = useState<StreamState>('connecting');
  const [paused, setPausedState] = useState(false);
  const [buffered, setBuffered] = useState(0);
  const [generator, setGenerator] = useState<GeneratorStatus | null>(null);
  const [held, setHeldState] = useState(false);
  const pausedRef = useRef(false);
  const heldRef = useRef(false);
  const bufferRef = useRef<LiveEvent[]>([]);

  useEffect(() => {
    let closed = false;
    getLiveSnapshot()
      .then((snap) => {
        if (closed) return;
        setEvents((prev) => mergeNewestFirst(prev, snap.events));
        setGenerator(snap.generator);
      })
      .catch(() => undefined);

    if (typeof EventSource === 'undefined') {
      setState('offline');
      return () => {
        closed = true;
      };
    }

    const es = new EventSource(liveStreamUrl());
    es.onopen = () => setState('live');
    es.onerror = () => setState(es.readyState === EventSource.CLOSED ? 'offline' : 'reconnecting');
    es.addEventListener('decision', (msg) => {
      let ev: LiveEvent;
      try {
        ev = JSON.parse((msg as MessageEvent<string>).data);
      } catch {
        return;
      }
      if (pausedRef.current || heldRef.current) {
        bufferRef.current.push(ev);
        setBuffered(bufferRef.current.length);
      } else {
        setEvents((prev) => mergeNewestFirst(prev, [ev]));
      }
    });

    return () => {
      closed = true;
      es.close();
    };
  }, []);

  const flushIfRunning = useCallback(() => {
    if (pausedRef.current || heldRef.current || bufferRef.current.length === 0) return;
    const pending = bufferRef.current;
    bufferRef.current = [];
    setBuffered(0);
    setEvents((prev) => mergeNewestFirst(prev, pending));
  }, []);

  /** Explicit user pause. */
  const setPaused = useCallback(
    (value: boolean) => {
      pausedRef.current = value;
      setPausedState(value);
      flushIfRunning();
    },
    [flushIfRunning],
  );

  /** Transient hold (e.g. while the pointer is over the feed) so rows don't move under the cursor. */
  const setHeld = useCallback(
    (value: boolean) => {
      heldRef.current = value;
      setHeldState(value);
      flushIfRunning();
    },
    [flushIfRunning],
  );

  // Keep generator status (emitted count, running flag) fresh.
  useEffect(() => {
    const id = window.setInterval(() => {
      getLiveSnapshot(1)
        .then((snap) => setGenerator(snap.generator))
        .catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(id);
  }, []);

  const clear = useCallback(() => setEvents([]), []);

  return { events, state, paused, setPaused, held, setHeld, buffered, clear, generator, setGenerator };
}
