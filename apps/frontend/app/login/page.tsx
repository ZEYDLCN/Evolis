"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken, ApiError } from "../../lib/api";
import { page, card, input, button, buttonSecondary, brand, errorText, mutedText } from "../../lib/styles";
import EvolisLogo from "../../components/EvolisLogo";

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
      <EvolisLogo size={44} showTagline />

      <form onSubmit={submit} style={{ ...card, marginTop: "2rem" }}>
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          <button type="button" onClick={() => setMode("login")} style={mode === "login" ? button : buttonSecondary}>
            Log in
          </button>
          <button type="button" onClick={() => setMode("register")} style={mode === "register" ? button : buttonSecondary}>
            Register
          </button>
        </div>

        <label style={{ fontSize: 13, color: brand.mutedGreen }}>Email</label>
        <input style={{ ...input, marginBottom: 12, marginTop: 4 }} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />

        <label style={{ fontSize: 13, color: brand.mutedGreen }}>Password</label>
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
