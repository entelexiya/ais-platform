/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    fontFamily: {
      sans: ['Rubik', 'system-ui', 'sans-serif'],
    },
    extend: {
      colors: {
        brand: {
          bg: '#1f1633',
          card: '#2a1f42',
          border: 'rgba(255,255,255,0.08)',
          lime: '#c2ef4e',
          'lime-dark': '#a8d63a',
          purple: '#7c3aed',
          muted: 'rgba(255,255,255,0.5)',
        },
        wa: {
          light: '#efeae2',
          header: '#f0f2f5',
          green: '#25D366',
          dark: '#111b21',
          panel: '#202c33'
        }
      },
      boxShadow: {
        'lime': '0 4px 24px rgba(194,239,78,0.25)',
        'card': '0 2px 16px rgba(0,0,0,0.3)',
      }
    },
  },
  plugins: [],
}
