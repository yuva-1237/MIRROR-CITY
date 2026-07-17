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
        brand: {
          dark: '#090d16',        // Deep space black
          panel: '#101625',       // Dark slate blue container
          border: '#1f293d',      // Slate border
          accent: '#2563eb',      // Royal blue
          neonCyan: '#06b6d4',    // GIS telemetry cyan
          neonGreen: '#10b981',   // Sustainability green
          neonPurple: '#8b5cf6',  // Comparison purple
          neonOrange: '#f97316',  // Alert Orange
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
