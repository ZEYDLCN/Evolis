"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "../../components/AppShell";
import ThemeToggle from "../../components/ThemeToggle";
import { useRequireAuth } from "../../lib/useAuth";
import { api, clearToken, Me } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";

export default function ProfilePage() {
  const ready = useRequireAuth();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    if (ready) api.me().then(setMe);
  }, [ready]);

  async function exportData() {
    const data = await api.exportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "evolis-export.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function deleteAccount() {
    if (!confirm("This permanently deletes your account and all data. Continue?")) return;
    await api.deleteAccount();
    clearToken();
    router.push("/login");
  }

  if (!ready) return null;

  return (
    <AppShell>
      <PageHeader title="Settings" description="Account, appearance, and privacy." />

      <Card className="mb-6">
        <div className="mb-3 text-sm font-semibold text-ink">Account</div>
        {me ? (
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted">Email</span>
              <span className="text-ink">{me.email}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-muted">Signed up</span>
              <span className="text-ink">{new Date(me.created_at).toLocaleDateString()}</span>
            </div>
            {me.google_linked && (
              <div className="flex items-center justify-between">
                <span className="text-muted">Sign-in method</span>
                <Badge tone="info">Google</Badge>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted">Loading...</p>
        )}
      </Card>

      <Card className="mb-6">
        <div className="mb-3 text-sm font-semibold text-ink">Appearance</div>
        <ThemeToggle />
      </Card>

      <Card>
        <div className="mb-3 text-sm font-semibold text-ink">Privacy</div>
        <p className="mb-3 text-xs text-muted">
          Your entries are yours. Export everything Evolis has stored about you, or permanently delete your account.
        </p>
        {me && (
          <div className="mb-3 flex items-center justify-between rounded-xl bg-surface px-3 py-2 text-sm">
            <span className="text-ink">Entry encryption at rest</span>
            <Badge tone={me.encryption_enabled ? "positive" : "neutral"}>{me.encryption_enabled ? "Enabled" : "Not enabled"}</Badge>
          </div>
        )}
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" onClick={exportData}>
            Export my data
          </Button>
          <Button variant="danger" onClick={deleteAccount}>
            Delete account
          </Button>
        </div>
      </Card>
    </AppShell>
  );
}
