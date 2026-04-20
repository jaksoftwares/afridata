/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/**/*.js",
    "./**/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: '#0B4F6C',    // Deep Ocean Blue
          teal: '#1B998B',    // Data Teal
          green: '#7BC67B',   // Soft Green
          grey: '#4A5568',    // Slate Grey
          offwhite: '#F7FAFC',
          amber: '#F2C14E',   // Warm Amber
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['IBM Plex Serif', 'serif'],
      },
      borderRadius: {
        'brand-btn': '8px',
        'brand-card': '12px',
      },
      boxShadow: {
        'brand-subtle': '0 2px 4px rgba(0, 0, 0, 0.05)',
      }
    },
  },
  plugins: [],
}
