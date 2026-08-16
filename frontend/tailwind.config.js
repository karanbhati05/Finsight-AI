/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        gain:       '#0f9d58',
        'gain-bg':  '#e6f4ea',
        loss:       '#d93025',
        'loss-bg':  '#fce8e6',
        primary:    '#1a73e8',
        'primary-hover': '#1557b0',
        surface:    '#f8f9fa',
        'surface-hover': '#f1f3f4',
        border:     '#e8eaed',
        text:       '#202124',
        subtext:    '#5f6368',
        muted:      '#80868b',
        'positive-text': '#137333',
        'positive-bg':   '#e6f4ea',
        'negative-text': '#c5221f',
        'negative-bg':   '#fce8e6',
        'neutral-text':  '#5f6368',
        'neutral-bg':    '#f1f3f4',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      fontSize: {
        '2xs': '11px',
      },
    },
  },
  plugins: [],
}
