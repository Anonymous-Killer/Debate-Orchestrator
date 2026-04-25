import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
    './hooks/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg:           '#08080f',
        surface:      '#0f0f1b',
        card:         '#161628',
        'card-hover': '#1c1c34',
        ink:          '#eeeef8',
        muted:        '#7070a0',
        dim:          '#3a3a58',
        'side-a':     '#e87848',
        'side-b':     '#48a8e0',
        cta:          '#7c5cfc',
        good:         '#3ec88a',
        warn:         '#f0a030',
        danger:       '#e04848',
      },
      fontFamily: {
        sans:    ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
      },
      animation: {
        'wave-bar':   'waveBar 0.5s ease-in-out infinite',
        'pulse-glow': 'glowPulse 1.5s ease infinite',
        'fade-in':    'fadeIn 0.5s ease both',
        'slide-left': 'slideLeft 0.5s ease both',
        'slide-right':'slideRight 0.5s ease both',
        'scale-in':   'scaleIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) both',
        'spin':       'spin 1s linear infinite',
      },
      keyframes: {
        waveBar:    { '0%,100%': { transform: 'scaleY(0.3)' }, '50%': { transform: 'scaleY(1)' } },
        glowPulse:  { '0%,100%': { boxShadow: '0 0 12px 2px var(--glow-color, rgba(124,92,252,0.5))' }, '50%': { boxShadow: '0 0 28px 6px var(--glow-color, rgba(124,92,252,0.5))' } },
        fadeIn:     { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        slideLeft:  { from: { opacity: '0', transform: 'translateX(-60px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
        slideRight: { from: { opacity: '0', transform: 'translateX(60px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
        scaleIn:    { from: { opacity: '0', transform: 'scale(0.85)' }, to: { opacity: '1', transform: 'scale(1)' } },
        spin:       { from: { transform: 'rotate(0deg)' }, to: { transform: 'rotate(360deg)' } },
      },
    },
  },
  plugins: [],
}

export default config
