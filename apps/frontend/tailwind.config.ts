import type { Config } from "tailwindcss";

// Evolis design tokens — see docs/ARCHITECTURE.md and the product proposal
// this implements. Brand greens are accents, not the whole UI: the base
// surface/text/border scale is deliberately neutral so green stays a
// signal (growth, success, primary actions) instead of wallpaper.
const config: Config = {
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
        surface: "#F8FAF9",
        card: "#FFFFFF",
        ink: "#102019",
        muted: "#6B7D73",
        line: "#E4ECE7",
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
