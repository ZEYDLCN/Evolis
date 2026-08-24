"use client";

import { useRouter } from "next/navigation";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, clearToken } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { PageHeader } from "../../components/ui/PageHeader";

export default function ProfilePage() {
  const ready = useRequireAuth();
  const router = useRouter();

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
      <PageHeader title="Profile" description="Account and privacy settings." />

      <Card>
        <div className="mb-3 text-sm font-semibold text-ink">Privacy</div>
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
