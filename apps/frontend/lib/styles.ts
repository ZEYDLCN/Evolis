import { CSSProperties } from "react";

export const page: CSSProperties = { maxWidth: 900, margin: "0 auto", padding: "0 1.5rem 4rem" };

export const card: CSSProperties = {
  border: "1px solid #eee",
  borderRadius: 10,
  padding: "1.25rem",
  marginBottom: "1rem",
};

export const input: CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid #ddd",
  fontSize: 15,
  boxSizing: "border-box",
};

export const button: CSSProperties = {
  padding: "10px 16px",
  borderRadius: 8,
  border: "none",
  background: "#111",
  color: "#fff",
  fontSize: 14,
  cursor: "pointer",
};

export const pill: CSSProperties = {
  display: "inline-block",
  padding: "3px 10px",
  borderRadius: 999,
  fontSize: 13,
  marginRight: 6,
  marginBottom: 6,
};

export const errorText: CSSProperties = { color: "#c0392b", fontSize: 14, marginTop: 8 };
export const mutedText: CSSProperties = { color: "#888", fontSize: 14 };
