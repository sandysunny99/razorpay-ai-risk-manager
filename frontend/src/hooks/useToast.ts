// frontend/src/hooks/useToast.ts
/**
 * Phase 5.2 — Toast Notification System
 * Replaces ALL alert() calls and console.error silences.
 * Types: success, error, warning, info, security
 * Auto-dismiss: 5s (info/success), 10s (warning), never (security)
 */
import { useCallback, useRef, useState } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info' | 'security';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  autoDismiss: boolean;
}

export interface UseToastResult {
  toasts: Toast[];
  showToast: (type: ToastType, title: string, message?: string) => void;
  dismissToast: (id: string) => void;
}

const AUTO_DISMISS_MS: Record<ToastType, number | null> = {
  success: 5000,
  info: 5000,
  warning: 10000,
  error: 8000,
  security: null, // Never auto-dismiss security alerts
};

export function useToast(): UseToastResult {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const showToast = useCallback(
    (type: ToastType, title: string, message?: string) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      const autoDismissMs = AUTO_DISMISS_MS[type];
      const toast: Toast = {
        id,
        type,
        title,
        message,
        autoDismiss: autoDismissMs !== null,
      };

      setToasts((prev) => [toast, ...prev].slice(0, 8)); // Max 8 stacked

      if (autoDismissMs !== null) {
        const timer = setTimeout(() => dismissToast(id), autoDismissMs);
        timersRef.current.set(id, timer);
      }
    },
    [dismissToast],
  );

  return { toasts, showToast, dismissToast };
}
