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
        // 🎨 CLINTRA ULTRA-DARK THEME - DRAMATIC & SMOOTH
        clintra: {
          // Ultra Dark Navy - Deeper, more dramatic backgrounds
          navy: '#0A0E13',
          'navy-light': '#141A20',
          'navy-lighter': '#1E252C',
          'navy-dark': '#050709',
          'navy-darker': '#020304',
          
          // Enhanced Vibrant Teal - Smoother gradients
          teal: '#00E6FF',
          'teal-bright': '#33F0FF',
          'teal-dark': '#00B8CC',
          'teal-darker': '#0099AA',
          
          // Electric Cyan - Enhanced brightness
          cyan: '#00FFFF',
          'cyan-bright': '#66FFFF',
          'cyan-dark': '#00CCCC',
          'cyan-darker': '#009999',
          
          // Deep Purple - More sophisticated
          purple: '#7C3AED',
          'purple-bright': '#A855F7',
          'purple-dark': '#5B21B6',
          'purple-darker': '#4C1D95',
          
          // Hot Pink - Refined
          pink: '#EC4899',
          'pink-bright': '#F472B6',
          'pink-dark': '#BE185D',
          'pink-darker': '#9D174D',
          
          // Rich Gold - Enhanced
          gold: '#FBBF24',
          'gold-bright': '#FCD34D',
          'gold-dark': '#D97706',
          'gold-darker': '#B45309',
          
          // New accent colors for better contrast
          silver: '#E5E7EB',
          'silver-dark': '#9CA3AF',
          emerald: '#10B981',
          'emerald-bright': '#34D399',
          'emerald-dark': '#059669',
        },
        
        // Mode-specific colors
        literature: {
          500: '#10B981',
          600: '#059669',
          700: '#047857',
        },
        hypothesis: {
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1E40AF',
        },
        download: {
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
        },
        
        primary: {
          50: '#eff6ff',
          500: '#00D9FF',
          600: '#00A8CC',
          700: '#008099',
        }
      }
    },
  },
  plugins: [],
}
