/** @type {import('tailwindcss').Config} */
// Tokens and the reason for each live in DESIGN.md. Semantic names only: no raw palette classes in components.
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#0e0f11',
        surface: '#15171a',
        raised: '#1d2024',
        line: { DEFAULT: '#2b2f35', strong: '#3d424a' },
        ink: { DEFAULT: '#ecebe7', muted: '#b4b2ac', subtle: '#908e88' },
        allow: '#6cc58f',
        review: '#e2a945',
        block: '#f0705f',
        zombie: '#b49cff',
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      borderRadius: { sm: '3px', DEFAULT: '5px', md: '6px' },
      keyframes: {
        'row-in': {
          '0%': { backgroundColor: 'rgba(236,235,231,0.10)' },
          '100%': { backgroundColor: 'rgba(236,235,231,0)' },
        },
      },
      animation: { 'row-in': 'row-in 900ms ease-out' },
    },
  },
  plugins: [],
}
