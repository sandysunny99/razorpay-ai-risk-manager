// frontend/src/components/ToastContainer.tsx
/**
 * Phase 5.2 — Toast Container Component
 * Renders stacked toasts in top-right corner.
 * Accessible: role="alert", aria-live="assertive" for security alerts.
 */
import React from 'react';
import type { Toast, ToastType } from '../hooks/useToast';

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

const TOAST_STYLES: Record<ToastType, string> = {
  success: 'border-emerald-500 bg-emerald-950/90 text-emerald-200',
  error:   'border-red-500 bg-red-950/90 text-red-200',
  warning: 'border-amber-500 bg-amber-950/90 text-amber-200',
  info:    'border-blue-500 bg-blue-950/90 text-blue-200',
  security: 'border-red-400 bg-red-950 text-red-100 shadow-red-500/40 shadow-lg animate-pulse-border',
};

const TOAST_ICONS: Record<ToastType, string> = {
  success:  '✓',
  error:    '✕',
  warning:  '⚠',
  info:     'ℹ',
  security: '🛡',
};

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="alert"
          aria-live={toast.type === 'security' ? 'assertive' : 'polite'}
          aria-atomic="true"
          className={`
            pointer-events-auto
            flex items-start gap-3
            rounded-lg border px-4 py-3
            backdrop-blur-md
            transition-all duration-300
            ${TOAST_STYLES[toast.type]}
          `}
        >
          {/* Icon */}
          <span className="text-lg leading-none mt-0.5 flex-shrink-0">
            {TOAST_ICONS[toast.type]}
          </span>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm leading-snug">{toast.title}</p>
            {toast.message && (
              <p className="text-xs opacity-80 mt-0.5 leading-relaxed">{toast.message}</p>
            )}
          </div>

          {/* Dismiss button */}
          <button
            onClick={() => onDismiss(toast.id)}
            className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity text-lg leading-none"
            aria-label="Dismiss notification"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
