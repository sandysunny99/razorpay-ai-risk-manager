import { useEffect } from 'react';

interface KeyboardShortcutHandlers {
  onOpenCommandPalette?: () => void;
  onResetDemo?: () => void;
  onGoldenDemo?: () => void;
  onCloseModals?: () => void;
  onSwitchTab?: (tabIndex: number) => void;
  onToggleShortcutsHelp?: () => void;
}

export function useKeyboardShortcuts(handlers: KeyboardShortcutHandlers) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't intercept if user is typing in an input or textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        if (event.key === 'Escape' && handlers.onCloseModals) {
          handlers.onCloseModals();
        }
        return;
      }

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const isCmdOrCtrl = isMac ? event.metaKey : event.ctrlKey;

      // ⌘K / Ctrl+K: Command Palette
      if (isCmdOrCtrl && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        handlers.onOpenCommandPalette?.();
        return;
      }

      // ⌘D / Ctrl+D: Golden Demo Scenario
      if (isCmdOrCtrl && event.key.toLowerCase() === 'd') {
        event.preventDefault();
        handlers.onGoldenDemo?.();
        return;
      }

      // ⌘R / Ctrl+R: Reset Data (intercept browser reload if Ctrl+Shift not held)
      if (isCmdOrCtrl && event.key.toLowerCase() === 'r' && !event.shiftKey) {
        event.preventDefault();
        handlers.onResetDemo?.();
        return;
      }

      // Escape: Close open modals
      if (event.key === 'Escape') {
        handlers.onCloseModals?.();
        return;
      }

      // ?: Help Modal
      if (event.key === '?') {
        event.preventDefault();
        handlers.onToggleShortcutsHelp?.();
        return;
      }

      // Number keys 1-9: Tab navigation
      if (/^[1-9]$/.test(event.key) && !isCmdOrCtrl && !event.altKey) {
        const tabIndex = parseInt(event.key, 10) - 1;
        handlers.onSwitchTab?.(tabIndex);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlers]);
}
