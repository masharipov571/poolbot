/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: '#090514',      // Deep dark space background
        darkCard: '#130b24',    // Translucent glassmorphic card base
        neonViolet: '#9d4edd',  // Active primary violet
        neonIndigo: '#5a189a',  // Glow indigo accent
        neonPink: '#ff007f',    // Secondary high-contrast select pink
      },
      fontFamily: {
        outfit: ['Outfit', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
