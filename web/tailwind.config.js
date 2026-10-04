/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--bg-canvas)',
        surface: 'var(--bg-surface)',
        elevated: 'var(--bg-elevated)',
        hover: 'var(--bg-hover)',
        inset: 'var(--bg-inset)',

        'border-subtle': 'var(--border-subtle)',
        'border-strong': 'var(--border-strong)',

        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',

        accent: {
          DEFAULT: 'var(--accent)',
          hover: 'var(--accent-hover)',
          subtle: 'var(--accent-subtle)',
          foreground: 'var(--on-accent)',
        },
        'on-accent': 'var(--on-accent)',

        success: {
          DEFAULT: 'var(--success)',
          subtle: 'var(--success-subtle)',
        },
        warning: {
          DEFAULT: 'var(--warning)',
          subtle: 'var(--warning-subtle)',
        },
        danger: {
          DEFAULT: 'var(--danger)',
          subtle: 'var(--danger-subtle)',
        },
        info: {
          DEFAULT: 'var(--info)',
          subtle: 'var(--info-subtle)',
        },
        draft: {
          DEFAULT: 'var(--draft)',
          subtle: 'var(--draft-subtle)',
        },
        'severity-high': 'var(--severity-high)',
        'diff-add': 'var(--diff-add-bg)',
        'diff-del': 'var(--diff-del-bg)',
        'focus-ring': 'var(--focus-ring)',
      },
      fontSize: {
        'caption': ['12px', { lineHeight: '16px' }],
        'dense': ['13px', { lineHeight: '18px' }],
        'body': ['14px', { lineHeight: '20px' }],
        'subhead': ['16px', { lineHeight: '24px' }],
        'title-3': ['20px', { lineHeight: '28px' }],
        'title-2': ['24px', { lineHeight: '32px' }],
        'title-1': ['32px', { lineHeight: '40px' }],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '8px',
        md: '8px',
        lg: '12px',
        xl: '12px',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      boxShadow: {
        popover: 'var(--shadow-popover)',
      },
      transitionTimingFunction: {
        standard: 'cubic-bezier(.2,.8,.2,1)',
      },
      transitionDuration: {
        fast: '120ms',
        normal: '200ms',
        slow: '320ms',
      },
    },
  },
  plugins: [],
};
