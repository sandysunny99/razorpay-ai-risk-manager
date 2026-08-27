export const tokens = {
  colors: {
    background: '#081220',
    surface: '#0B192C',
    surfaceSubtle: '#1E293B',
    border: '#1E293B',
    borderSubtle: '#334155',
    textPrimary: '#F8FAFC',
    textSecondary: '#94A3B8',
    textMuted: '#64748B',
    accent: '#3B82F6',
    accentHover: '#2563EB',
  },
  threatLevels: {
    critical: { bg: '#450A0A', border: '#EF4444', text: '#FCA5A5' },
    high:     { bg: '#431407', border: '#F97316', text: '#FDBA74' },
    medium:   { bg: '#422006', border: '#EAB308', text: '#FDE047' },
    low:      { bg: '#052E16', border: '#22C55E', text: '#86EFAC' },
  },
  animations: {
    pulse:   'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    fadeIn:  'fadeIn 200ms ease-out',
    slideUp: 'slideUp 300ms cubic-bezier(0.16, 1, 0.3, 1)',
  },
  zIndex: {
    commandPalette: 9999,
    modal:          1000,
    sidebar:        100,
    header:         50,
  },
} as const;

export default tokens;
