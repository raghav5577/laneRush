/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        lane: {
          dark: '#0B0F17',
          card: '#131A26',
          border: '#1E293B',
          accent: '#3B82F6',
          green: '#10B981',
          yellow: '#F59E0B',
          red: '#EF4444',
          ev: '#FF2E4D',
        }
      }
    },
  },
  plugins: [],
}
