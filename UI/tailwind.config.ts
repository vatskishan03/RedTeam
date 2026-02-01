import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Background colors
        'bg-primary': '#0d1117',
        'bg-secondary': '#161b22',
        'bg-tertiary': '#21262d',
        
        // Text colors
        'text-primary': '#f0f6fc',
        'text-secondary': '#8b949e',
        
        // Agent colors
        'agent-attacker': '#f85149',
        'agent-defender': '#3fb950',
        'agent-arbiter': '#d29922',
        'agent-reporter': '#58a6ff',
        
        // Border
        'border-default': '#30363d',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'typing': 'typing 0.5s steps(1) infinite',
        'glow-red': 'glowRed 2s ease-in-out infinite',
        'glow-green': 'glowGreen 2s ease-in-out infinite',
        'glow-yellow': 'glowYellow 2s ease-in-out infinite',
        'glow-blue': 'glowBlue 2s ease-in-out infinite',
      },
      keyframes: {
        typing: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        glowRed: {
          '0%, 100%': { boxShadow: '0 0 5px #f85149, 0 0 10px #f85149' },
          '50%': { boxShadow: '0 0 20px #f85149, 0 0 30px #f85149' },
        },
        glowGreen: {
          '0%, 100%': { boxShadow: '0 0 5px #3fb950, 0 0 10px #3fb950' },
          '50%': { boxShadow: '0 0 20px #3fb950, 0 0 30px #3fb950' },
        },
        glowYellow: {
          '0%, 100%': { boxShadow: '0 0 5px #d29922, 0 0 10px #d29922' },
          '50%': { boxShadow: '0 0 20px #d29922, 0 0 30px #d29922' },
        },
        glowBlue: {
          '0%, 100%': { boxShadow: '0 0 5px #58a6ff, 0 0 10px #58a6ff' },
          '50%': { boxShadow: '0 0 20px #58a6ff, 0 0 30px #58a6ff' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}

export default config
