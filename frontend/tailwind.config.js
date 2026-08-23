/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        razorpay: {
          dark: '#0C2340',
          navy: '#0B192C',
          blue: '#0D83FF',
          accent: '#1E40AF',
          lightBlue: '#E6F0FF',
          surface: '#1E293B',
          surfaceLight: '#334155',
          border: '#334155',
        },
        risk: {
          low: '#10B981',
          medium: '#F59E0B',
          high: '#F97316',
          critical: '#EF4444',
        }
      }
    },
  },
  plugins: [],
}
