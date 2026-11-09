import { createContext, ReactNode, useContext } from 'react';
import { useLiveStream } from './useLiveStream';

type LiveValue = ReturnType<typeof useLiveStream>;

const LiveContext = createContext<LiveValue | null>(null);

/** One SSE connection for the whole app: pages, the top bar and the command palette share it. */
export function LiveProvider({ children }: { children: ReactNode }) {
  const value = useLiveStream();
  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>;
}

export function useLive(): LiveValue {
  const ctx = useContext(LiveContext);
  if (!ctx) throw new Error('useLive must be used inside <LiveProvider>');
  return ctx;
}
