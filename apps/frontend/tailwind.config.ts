import type { Config } from "tailwindcss";

// Evolis design tokens — see docs/ARCHITECTURE.md and the product proposal
// this implements. Brand greens are accents, not the whole UI: the base
// surface/text/border scale is deliberately neutral so green stays a
// signal (growth, success, primary actions) instead of wallpaper.
// Neutral tokens (surface/card/ink/muted/line) are CSS variables so Dark
// Mode (section 47) can repaint them from globals.css without touching a
// single component — every component already uses the semantic class name
// (bg-surface, text-ink, ...) rather than a raw hex. Brand greens stay
// fixed across themes; they're accents, already vibrant enough to read on
// both a light and a dark neutral base.
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          forest: "#0B2A1E",
          emerald: "#168B62",
          mid: "#4AAE70",
          lime: "#C7F36A",
        },
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        card: "rgb(var(--color-card) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        line: "rgb(var(--color-line) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "Manrope", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl: "14px",
        "2xl": "20px",
      },
    },
  },
  plugins: [],
};

export default config;
