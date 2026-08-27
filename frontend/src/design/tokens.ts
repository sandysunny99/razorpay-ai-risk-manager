// frontend/src/design/tokens.ts
/**
 * Razorpay AI Risk Manager — SOC-Grade Design Tokens
 * Enterprise-grade, information-dense, dark security operations theme.
 */

export const tokens = {
  color: {
    bg: {
      canvas: '#0A0D12',   // Deepest background — near-black with blue cast
      surface: '#111827',  // Card/panel surface
      raised: '#1E2538',   // Elevated elements, dropdowns
      overlay: '#252D3D',  // Modals, tooltips
      hover: '#2A3347',    // Interactive hover state
    },
    risk: {
      critical: '#EF4444',    // Immediate threat — red-500
      criticalBg: 'rgba(239,68,68,0.1)',
      high: '#F97316',        // Elevated risk — orange-500
      highBg: 'rgba(249,115,22,0.1)',
      medium: '#EAB308',      // Watch — yellow-500
      mediumBg: 'rgba(234,179,8,0.1)',
      low: '#22C55E',         // Safe — green-500
      lowBg: 'rgba(34,197,94,0.1)',
      neutral: '#64748B',     // No signal — slate-500
    },
    accent: {
      primary: '#3B82F6',     // Razorpay blue — blue-500
      glow: 'rgba(59,130,246,0.15)',
      pulse: 'rgba(59,130,246,0.4)',
    },
    text: {
      primary: '#F1F5F9',     // slate-100
      secondary: '#94A3B8',   // slate-400
      muted: '#475569',       // slate-600
      code: '#7DD3FC',        // sky-300 (for IDs, hashes)
    },
    border: {
      subtle: 'rgba(255,255,255,0.05)',
      default: 'rgba(255,255,255,0.10)',
      strong: 'rgba(255,255,255,0.20)',
      accent: 'rgba(59,130,246,0.30)',
    },
    status: {
      dryRun: '#F59E0B',      // amber-500 — prominent DRY_RUN badge
      live: '#10B981',        // emerald-500 — pulsing live indicator
      connected: '#22C55E',
      error: '#EF4444',
    },
  },
  font: {
    display: '"JetBrains Mono", "Fira Code", monospace',
    body: '"Inter", "DM Sans", system-ui, sans-serif',
    code: '"JetBrains Mono", monospace',
  },
  radius: {
    sm: '6px',
    md: '10px',
    lg: '14px',
    xl: '20px',
  },
  shadow: {
    card: '0 1px 3px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)',
    glow: '0 0 20px rgba(59,130,246,0.15)',
    risk: '0 0 16px rgba(239,68,68,0.25)',
  },
};
