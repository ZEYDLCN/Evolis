"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken, ApiError } from "../../lib/api";
import { page, card, input, button, errorText, mutedText } from "../../lib/styles";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = mode === "login" ? await api.login(email, password) : await api.register(email, password);
      setToken(result.access_token);
      router.push("/today");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ ...page, maxWidth: 420, paddingTop: "4rem" }}>
      <h1 style={{ marginBottom: 4 }}>LifeDiff</h1>
      <p style={mutedText}>Version Control for Your Life</p>

      <form onSubmit={submit} style={{ ...card, marginTop: "2rem" }}>
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          <button
            type="button"
            onClick={() => setMode("login")}
            style={{ ...button, background: mode === "login" ? "#111" : "#eee", color: mode === "login" ? "#fff" : "#333" }}
          >
            Log in
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            style={{ ...button, background: mode === "register" ? "#111" : "#eee", color: mode === "register" ? "#fff" : "#333" }}
          >
            Register
          </button>
        </div>

        <label style={{ fontSize: 13, color: "#666" }}>Email</label>
        <input style={{ ...input, marginBottom: 12, marginTop: 4 }} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />

        <label style={{ fontSize: 13, color: "#666" }}>Password</label>
        <input
          style={{ ...input, marginBottom: 16, marginTop: 4 }}
          type="password"
          required
          minLength={6}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button type="submit" style={{ ...button, width: "100%" }} disabled={loading}>
          {loading ? "..." : mode === "login" ? "Log in" : "Create account"}
        </button>

        {error && <p style={errorText}>{error}</p>}
      </form>
    </main>
  );
}
