"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken, ApiError } from "../../lib/api";
import { cn } from "../../lib/cn";
import EvolisLogo from "../../components/EvolisLogo";
import GoogleSignInButton from "../../components/GoogleSignInButton";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input, Label } from "../../components/ui/Input";
import { useLang } from "../../components/LangProvider";

export default function LoginPage() {
  const router = useRouter();
  const { t } = useLang();
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
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const handleGoogleSuccess = useCallback(() => router.push("/dashboard"), [router]);
  const handleGoogleError = useCallback((message: string) => setError(message), []);

  return (
    <main className="mx-auto min-h-screen max-w-md bg-surface px-4 pt-16">
      <EvolisLogo size={44} showTagline />

      <Card className="mt-8">
        <div className="mb-4 flex gap-2">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={cn(
              "flex-1 rounded-xl py-2.5 text-sm font-semibold transition-colors",
              mode === "login" ? "bg-brand-emerald text-white" : "bg-surface text-ink"
            )}
          >
            {t("login.login")}
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={cn(
              "flex-1 rounded-xl py-2.5 text-sm font-semibold transition-colors",
              mode === "register" ? "bg-brand-emerald text-white" : "bg-surface text-ink"
            )}
          >
            {t("login.register")}
          </button>
        </div>

        <form onSubmit={submit}>
          <Label>{t("login.email")}</Label>
          <Input className="mb-3" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />

          <Label>{t("login.password")}</Label>
          <Input className="mb-4" type="password" required minLength={6} value={password} onChange={(e) => setPassword(e.target.value)} />

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "..." : mode === "login" ? t("login.login") : t("login.createAccount")}
          </Button>

          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </form>

        <GoogleSignInButton onSuccess={handleGoogleSuccess} onError={handleGoogleError} />
      </Card>
    </main>
  );
}
