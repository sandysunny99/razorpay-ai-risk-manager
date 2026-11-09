/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        'row-in': {
          '0%': { opacity: '0', transform: 'translateY(-4px)', backgroundColor: 'rgba(99,102,241,0.18)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: { 'row-in': 'row-in 600ms ease-out' },
    },
  },
  plugins: [],
}
