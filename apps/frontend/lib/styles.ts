import { CSSProperties } from "react";

// Evolis brand palette (from apps/frontend/public/brand/).
export const brand = {
  deepForest: "#0B2A1E",
  emerald: "#168B62",
  midGreen: "#4AAE70",
  lime: "#C7F36A",
  // Tints derived from the brand greens, used for surfaces/borders so the
  // whole app reads as one palette instead of brand-green-on-generic-gray.
  surfaceTint: "#F4FAF6",
  borderTint: "#DCEDE3",
  mutedGreen: "#5C7A6C",
  limeTint: "#F1FADD",
};

export const page: CSSProperties = { maxWidth: 900, margin: "0 auto", padding: "0 1.5rem 4rem" };

export const card: CSSProperties = {
  border: `1px solid ${brand.borderTint}`,
  borderRadius: 12,
  padding: "1.25rem",
  marginBottom: "1rem",
  background: "#ffffff",
};

export const input: CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: `1px solid ${brand.borderTint}`,
  fontSize: 15,
  boxSizing: "border-box",
  background: "#ffffff",
  color: brand.deepForest,
};

export const button: CSSProperties = {
  padding: "10px 16px",
  borderRadius: 8,
  border: "none",
  background: brand.emerald,
  color: "#ffffff",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};

export const buttonSecondary: CSSProperties = {
  ...button,
  background: brand.surfaceTint,
  color: brand.deepForest,
  border: `1px solid ${brand.borderTint}`,
};

export const pill: CSSProperties = {
  display: "inline-block",
  padding: "3px 10px",
  borderRadius: 999,
  fontSize: 13,
  marginRight: 6,
  marginBottom: 6,
  background: brand.surfaceTint,
  color: brand.deepForest,
};

export const errorText: CSSProperties = { color: "#c0392b", fontSize: 14, marginTop: 8 };
export const mutedText: CSSProperties = { color: brand.mutedGreen, fontSize: 14 };
